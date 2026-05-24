from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.domain.matrix import MatrixPlan
from mj_prompt_studio.domain.prompt_document import PromptDocument, PromptPatch
from mj_prompt_studio.domain.reference import ReferenceAsset, ResultImage, ResultReview
from mj_prompt_studio.infra.sqlite_repository import ProjectRecord
from mj_prompt_studio.ui.strings import APP_TITLE
from mj_prompt_studio.ui.widgets.ai_inspector import AIInspector
from mj_prompt_studio.ui.widgets.composer_widget import ComposerWidget
from mj_prompt_studio.ui.widgets.free_editor_widget import FreeEditorWidget
from mj_prompt_studio.ui.widgets.jobs_panel import JobsPanel
from mj_prompt_studio.ui.widgets.matrix_lab_widget import MatrixLabWidget
from mj_prompt_studio.ui.widgets.parameter_inspector import ParameterInspector
from mj_prompt_studio.ui.widgets.prompt_doctor_panel import PromptDoctorPanel
from mj_prompt_studio.ui.widgets.reference_library_widget import ReferenceLibraryWidget
from mj_prompt_studio.ui.widgets.result_review_widget import ResultReviewWidget
from mj_prompt_studio.ui.widgets.settings_widget import SettingsWidget


class JobBridge(QObject):
    completed = Signal(str, dict)


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.project, self.document = context.ensure_workspace()
        self.references: dict[str, ReferenceAsset] = {}
        self.pending_patches: list[PromptPatch] = []
        self.result_images: dict[str, ResultImage] = {}
        self.result_reviews: dict[str, ResultReview] = {}
        self.last_result_image: ResultImage | None = None
        self.last_review: ResultReview | None = None
        self.matrix_plan: MatrixPlan | None = None
        self.bridge = JobBridge()
        self.bridge.completed.connect(self._handle_job_completed)
        self.setWindowTitle(APP_TITLE)
        self.resize(1680, 980)
        self._apply_theme()
        self._build_toolbar()
        self._build_left_dock()
        self._build_central_tabs()
        self._build_right_dock()
        self._build_bottom_dock()
        self._refresh_all()

    def _apply_theme(self) -> None:
        qss = resources.files("mj_prompt_studio.ui.themes").joinpath("dark.qss").read_text()
        self.setStyleSheet(qss)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        actions = [
            ("新規プロジェクト", self._new_project),
            ("開く", self._open_project_dialog),
            ("保存", self._save_current_document),
            ("エクスポート", self._export_markdown_record_file),
            ("設定", lambda: self.tabs.setCurrentWidget(self.settings_widget)),
        ]
        for label, handler in actions:
            action = QAction(label, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("● AI接続中"))

    def _build_left_dock(self) -> None:
        dock = QDockWidget("プロジェクト", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        container = QWidget()
        layout = QVBoxLayout(container)
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("プロジェクト")
        self.history_list = QListWidget()
        self.quick_actions = QWidget()
        quick_layout = QVBoxLayout(self.quick_actions)
        for label, handler in [
            ("AI Brief作成", lambda: self.tabs.setCurrentWidget(self.composer_widget)),
            ("参照画像を追加", lambda: self.tabs.setCurrentWidget(self.reference_widget)),
            ("プロンプト比較", lambda: self.tabs.setCurrentWidget(self.result_widget)),
            ("マトリクス実験", lambda: self.tabs.setCurrentWidget(self.matrix_widget)),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            quick_layout.addWidget(button)
        layout.addWidget(self.project_tree, 3)
        layout.addWidget(QLabel("プロンプト履歴"))
        layout.addWidget(self.history_list, 2)
        layout.addWidget(QLabel("クイックアクション"))
        layout.addWidget(self.quick_actions, 2)
        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _build_central_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.composer_widget = ComposerWidget()
        self.free_editor_widget = FreeEditorWidget()
        self.matrix_widget = MatrixLabWidget()
        self.reference_widget = ReferenceLibraryWidget()
        self.result_widget = ResultReviewWidget()
        self.settings_widget = SettingsWidget(self.context)
        self.tabs.addTab(self.composer_widget, "Composer")
        self.tabs.addTab(self.free_editor_widget, "Free Editor")
        self.tabs.addTab(self.matrix_widget, "Matrix Lab")
        self.tabs.addTab(self.reference_widget, "Reference Library")
        self.tabs.addTab(self.result_widget, "Result Review")
        self.tabs.addTab(self.settings_widget, "Settings")
        self.setCentralWidget(self.tabs)
        self.composer_widget.brief_requested.connect(self._run_ai_brief)
        self.composer_widget.compile_requested.connect(self._compile_current_document)
        self.composer_widget.vocabulary_requested.connect(self._run_vocabulary)
        self.composer_widget.copy_button.clicked.connect(self._copy_prompt)
        self.matrix_widget.plan_requested.connect(self._run_matrix_plan)
        self.matrix_widget.generate_requested.connect(self._generate_matrix_variants)
        self.matrix_widget.copy_selected_requested.connect(self._copy_selected_matrix_variant)
        self.matrix_widget.copy_all_requested.connect(self._copy_all_matrix_variants)
        self.matrix_widget.csv_button.clicked.connect(self._copy_matrix_csv)
        self.matrix_widget.markdown_button.clicked.connect(self._copy_matrix_markdown)
        self.reference_widget.import_requested.connect(self._import_reference)
        self.reference_widget.analyze_requested.connect(self._analyze_reference)
        self.reference_widget.delete_requested.connect(self._delete_reference)
        self.reference_widget.tags_save_requested.connect(self._save_reference_tags)
        self.reference_widget.vocabulary_insert_requested.connect(self._insert_reference_vocabulary)
        self.result_widget.import_requested.connect(self._import_result_image)
        self.result_widget.review_requested.connect(self._run_result_review)
        self.result_widget.compare_requested.connect(self._compare_results)
        self.result_widget.next_prompt_requested.connect(self._send_next_prompt_to_composer)
        self.result_widget.audit_requested.connect(self._run_final_audit)

    def _build_right_dock(self) -> None:
        dock = QDockWidget("AI Inspector", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.ai_inspector = AIInspector()
        self.parameter_inspector = ParameterInspector(self.context.ruleset)
        self.prompt_doctor_panel = PromptDoctorPanel()
        splitter.addWidget(self.ai_inspector)
        splitter.addWidget(self.parameter_inspector)
        splitter.addWidget(self.prompt_doctor_panel)
        dock.setWidget(splitter)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.parameter_inspector.apply_button.clicked.connect(self._apply_parameters_from_inspector)
        self.prompt_doctor_panel.run_button.clicked.connect(self._run_prompt_doctor)
        self.prompt_doctor_panel.apply_patch_requested.connect(self._apply_selected_patch)

    def _build_bottom_dock(self) -> None:
        dock = QDockWidget("Status / Jobs / Validation", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.jobs_panel = JobsPanel(self.context.job_queue)
        self.jobs_panel.cancel_requested.connect(self._cancel_job)
        self.jobs_panel.retry_requested.connect(self._retry_job)
        dock.setWidget(self.jobs_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.statusBar().showMessage(
            f"保存済み | Current Ruleset: {self.context.ruleset.display_name}"
        )

    def _refresh_all(self) -> None:
        self.composer_widget.update_document(self.document)
        self.parameter_inspector.set_parameters(self.document.parameters)
        self.ai_inspector.update_document(self.document, self.document.validation_report)
        self.prompt_doctor_panel.set_validation_report(self.document.validation_report)
        self._refresh_project_tree()
        self._refresh_history()
        self._refresh_references()
        self._refresh_results()

    def _refresh_project_tree(self) -> None:
        self.project_tree.clear()
        root = QTreeWidgetItem([self.project.name])
        brief = QTreeWidgetItem(["Brief / 方向性"])
        brief.addChild(QTreeWidgetItem([self.document.title]))
        root.addChild(brief)
        for section in ["Product Photo", "Architecture", "Nature", "Character"]:
            root.addChild(QTreeWidgetItem([section]))
        self.project_tree.addTopLevelItem(root)
        self.project_tree.expandAll()

    def _refresh_history(self) -> None:
        self.history_list.clear()
        for revision in self.context.repository.list_prompt_revisions(self.document.id)[-8:]:
            label = (
                f"rev {revision['revision_number']} | "
                f"{revision['source']} | {revision['created_at']}"
            )
            self.history_list.addItem(label)

    def _refresh_references(self) -> None:
        references = self.context.repository.list_references(self.project.id)
        self.references = {reference.id: reference for reference in references}
        self.reference_widget.set_references(references)

    def _refresh_results(self) -> None:
        images = self.context.repository.list_result_images(self.project.id, self.document.id)
        self.result_images = {image.id: image for image in images}
        labels = [
            f"{Path(image.local_path).name} | {image.created_at.isoformat()}" for image in images
        ]
        self.result_widget.set_result_images(labels)

    def _new_project(self) -> None:
        name, ok = QInputDialog.getText(self, APP_TITLE, "プロジェクト名")
        if not ok:
            return
        project_name = name.strip() or "New Prompt Project"
        self.project, self.document = self.context.prompt_service.create_project_with_document(
            project_name, "Untitled Prompt"
        )
        self._refresh_all()

    def _open_project_dialog(self) -> None:
        projects = self.context.repository.list_projects()
        if not projects:
            QMessageBox.information(self, APP_TITLE, "開けるプロジェクトがありません。")
            return
        labels = [project.name for project in projects]
        label, ok = QInputDialog.getItem(self, APP_TITLE, "プロジェクトを開く", labels, 0, False)
        if not ok:
            return
        project = projects[labels.index(label)]
        self._load_project(project)

    def _load_project(self, project: ProjectRecord) -> None:
        documents = self.context.repository.list_prompt_documents(project.id)
        if not documents:
            document = PromptDocument.create(
                project.id, "Untitled Prompt", self.context.ruleset.ruleset_id
            )
            self.context.repository.save_prompt_document(document)
            self.context.repository.save_prompt_revision(document, "manual", "空ドキュメントを作成")
        else:
            document = documents[0]
        self.project = project
        self.document = document
        self._refresh_all()

    def _save_current_document(self) -> None:
        self.document.blocks = self.composer_widget.read_blocks()
        self.document.parameters = self.parameter_inspector.read_parameters()
        self.context.prompt_service.compile_document(
            self.document, source="manual", diff_summary="手動保存"
        )
        self._refresh_all()

    def _compile_current_document(self) -> None:
        self.document.blocks = self.composer_widget.read_blocks()
        self.document.parameters = self.parameter_inspector.read_parameters()
        self.context.prompt_service.compile_document(
            self.document, source="manual", diff_summary="Compile"
        )
        self._refresh_all()

    def _apply_parameters_from_inspector(self) -> None:
        self.document.parameters = self.parameter_inspector.read_parameters()
        self._compile_current_document()

    def _run_ai_brief(self, brief: str) -> None:
        if not brief:
            QMessageBox.information(self, APP_TITLE, "AI Briefに入力してください。")
            return

        def work() -> dict[str, Any]:
            document, result = self.context.prompt_service.build_from_brief(self.document, brief)
            return {"document": document.to_dict(), "agent": result.output_json}

        self.context.submit_agent_job(
            "IntentIntakeAgent",
            {"brief": brief},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _run_vocabulary(self, text: str) -> None:
        if not text:
            return

        def work() -> dict[str, Any]:
            return self.context.prompt_service.request_vocabulary(text).output_json

        self.context.submit_agent_job(
            "VocabularyAgent",
            {"text": text},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _run_prompt_doctor(self) -> None:
        self._compile_current_document()

        def work() -> dict[str, Any]:
            return self.context.prompt_service.run_prompt_doctor(self.document).output_json

        self.context.submit_agent_job(
            "PromptDoctorAgent",
            {"document_id": self.document.id},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _run_matrix_plan(self, objective: str) -> None:
        if not objective:
            objective = "商用利用に耐える朝食ビジュアルのスタイル比較"

        def work() -> dict[str, Any]:
            plan = self.context.matrix_service.plan_experiment(objective)
            return {"plan": plan.to_dict()}

        self.context.submit_agent_job(
            "MatrixPlannerAgent",
            {"objective": objective},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _generate_matrix_variants(self) -> None:
        if self.matrix_plan is None:
            QMessageBox.information(self, APP_TITLE, "先に実験計画を作成してください。")
            return
        variants = self.context.matrix_service.generate_and_save(
            self.project.id, self.matrix_plan, self.document.compiled_prompt
        )
        self.matrix_widget.set_variants(variants)

    def _import_reference(self, path: str) -> None:
        reference = self.context.reference_service.import_reference(self.project.id, Path(path))
        self._refresh_references()
        QMessageBox.information(self, APP_TITLE, f"参照素材を取り込みました: {reference.name}")

    def _analyze_reference(self, reference_id: str) -> None:
        reference = self.references.get(reference_id)
        if reference is None:
            return

        def work() -> dict[str, Any]:
            analyzed = self.context.reference_service.analyze_reference(reference)
            return {"reference": analyzed.to_dict()}

        self.context.submit_agent_job(
            "ReferenceAnalyzerAgent",
            {"reference_id": reference_id},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _delete_reference(self, reference_id: str) -> None:
        reference = self.references.get(reference_id)
        if reference is None:
            return
        answer = QMessageBox.question(
            self,
            APP_TITLE,
            f"参照素材「{reference.name}」を削除しますか?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.context.reference_service.delete_reference(reference_id)
        self._refresh_references()

    def _save_reference_tags(self, reference_id: str, tags: list[str]) -> None:
        reference = self.references.get(reference_id)
        if reference is None:
            return
        reference.tags = tags
        self.context.reference_service.update_reference(reference)
        self._refresh_references()

    def _insert_reference_vocabulary(self, vocabulary: str) -> None:
        old_value = self.document.blocks.style
        patch = PromptPatch(
            field_path="blocks.style",
            old_value=old_value,
            new_value=", ".join(item for item in [old_value, vocabulary] if item),
            reason="参照素材から抽出した語彙をStyleへ追加",
            confidence=0.9,
            requires_user_confirmation=True,
        )
        self._confirm_and_apply_patch(patch)

    def _import_result_image(self, path: str) -> None:
        self._compile_current_document()
        self.last_result_image = self.context.result_review_service.import_result_image(
            self.document, Path(path)
        )
        self.result_widget.add_result_image(Path(path).name)
        self._refresh_results()

    def _run_result_review(self) -> None:
        if self.last_result_image is None:
            QMessageBox.information(self, APP_TITLE, "先に生成結果画像を取り込んでください。")
            return
        result_image = self.last_result_image

        def work() -> dict[str, Any]:
            review = self.context.result_review_service.review_result(result_image)
            return {"review": review.to_dict()}

        self.context.submit_agent_job(
            "ResultReviewAgent",
            {"result_image_id": result_image.id},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _run_final_audit(self) -> None:
        self._compile_current_document()

        def work() -> dict[str, Any]:
            return self.context.result_review_service.final_audit(self.document).output_json

        self.context.submit_agent_job(
            "FinalAuditorAgent",
            {"document_id": self.document.id},
            work,
            callback=lambda job: self.bridge.completed.emit(job.agent_name, job.output_json or {}),
        )

    def _copy_prompt(self) -> None:
        QApplication.clipboard().setText(self.document.compiled_prompt)
        self.statusBar().showMessage("Compiled Promptをコピーしました")

    def _copy_markdown_record(self) -> None:
        QApplication.clipboard().setText(
            self.context.export_service.markdown_record(self.document, self.context.ruleset)
        )
        self.statusBar().showMessage("Markdown recordをコピーしました")

    def _copy_matrix_csv(self) -> None:
        QApplication.clipboard().setText(
            self.context.matrix_service.export_csv(self.matrix_widget.variants)
        )

    def _copy_matrix_markdown(self) -> None:
        if self.matrix_plan:
            QApplication.clipboard().setText(
                self.context.matrix_service.export_markdown(
                    self.matrix_plan, self.matrix_widget.variants
                )
            )

    def _handle_job_completed(self, agent_name: str, payload: dict[str, Any]) -> None:
        if agent_name == "IntentIntakeAgent":
            self.document = PromptDocument.from_dict(payload["document"])
            self.composer_widget.set_suggestions(payload.get("agent", {}))
        elif agent_name == "VocabularyAgent":
            self.composer_widget.set_suggestions(payload)
            patches = payload.get("patches")
            if isinstance(patches, list) and patches:
                self.pending_patches = [PromptPatch.from_dict(patch) for patch in patches]
                self.prompt_doctor_panel.set_agent_result(payload)
        elif agent_name == "PromptDoctorAgent":
            patches = payload.get("patches")
            if isinstance(patches, list):
                self.pending_patches = [PromptPatch.from_dict(patch) for patch in patches]
            self.prompt_doctor_panel.set_agent_result(payload)
            self.ai_inspector.update_agent_result(payload)
        elif agent_name == "MatrixPlannerAgent":
            self.matrix_plan = MatrixPlan.from_dict(payload["plan"])
            self.matrix_widget.set_plan(self.matrix_plan)
        elif agent_name == "ReferenceAnalyzerAgent":
            reference = ReferenceAsset.from_dict(payload["reference"])
            self.references[reference.id] = reference
            self._refresh_references()
        elif agent_name == "ResultReviewAgent":
            review = ResultReview.from_dict(payload["review"])
            self.last_review = review
            self.result_reviews[review.id] = review
            self.result_widget.set_review(review)
        elif agent_name == "FinalAuditorAgent":
            self.result_widget.set_audit(payload)
        self._refresh_all()
        self.jobs_panel.refresh()

    def _apply_selected_patch(self, index: int) -> None:
        if index < 0 or index >= len(self.pending_patches):
            return
        self._confirm_and_apply_patch(self.pending_patches[index])

    def _confirm_and_apply_patch(self, patch: PromptPatch) -> None:
        message = "\n".join(
            [
                patch.reason,
                "",
                f"対象: {patch.field_path}",
                f"変更前: {patch.old_value}",
                f"変更後: {patch.new_value}",
            ]
        )
        answer = QMessageBox.question(self, APP_TITLE, message)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.document = self.context.prompt_service.apply_patch(self.document, patch)
        self._refresh_all()

    def _compare_results(self) -> None:
        reviews: list[ResultReview] = []
        for image in self.result_images.values():
            reviews.extend(self.context.repository.list_result_reviews(image.id))
        if not reviews:
            QMessageBox.information(self, APP_TITLE, "比較できるレビューがありません。")
            return
        lines = ["Result Comparison", ""]
        for review in reviews:
            score = review.scores.get("commercial_usability", 0.0)
            lines.append(f"- {review.result_image_id}: commercial usability {score}")
            lines.append(f"  {review.ai_summary}")
        self.result_widget.set_comparison(lines)

    def _send_next_prompt_to_composer(self, candidate: str) -> None:
        patch = PromptPatch(
            field_path="blocks.notes",
            old_value=self.document.blocks.notes,
            new_value=candidate,
            reason="Result Reviewの改善候補をComposerへ戻す",
            confidence=0.82,
            requires_user_confirmation=True,
        )
        self._confirm_and_apply_patch(patch)

    def _copy_selected_matrix_variant(self) -> None:
        variant = self.matrix_widget.selected_variant()
        if variant is None:
            QMessageBox.information(self, APP_TITLE, "コピーするVariantを選択してください。")
            return
        QApplication.clipboard().setText(variant.prompt)
        self.statusBar().showMessage("選択Variantをコピーしました")

    def _copy_all_matrix_variants(self) -> None:
        prompts = "\n".join(variant.prompt for variant in self.matrix_widget.variants)
        QApplication.clipboard().setText(prompts)
        self.statusBar().showMessage("Matrix variantsを一括コピーしました")

    def _export_markdown_record_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Markdown recordを保存",
            f"{self.document.title}.md",
            "Markdown (*.md)",
        )
        if not path:
            return
        self.context.export_to_file(
            Path(path),
            lambda: self.context.export_service.markdown_record(
                self.document, self.context.ruleset
            ),
        )
        self.statusBar().showMessage(f"Markdown recordを保存しました: {path}")

    def _cancel_job(self, job_id: str) -> None:
        if not self.context.job_queue.cancel(job_id):
            QMessageBox.information(self, APP_TITLE, "実行中のJobはキャンセルできませんでした。")
        self.jobs_panel.refresh()

    def _retry_job(self, job_id: str) -> None:
        try:
            self.context.job_queue.retry(job_id)
        except Exception as exc:
            QMessageBox.information(self, APP_TITLE, f"再実行できません: {exc}")
        self.jobs_panel.refresh()

    def _info_not_implemented(self) -> None:
        QMessageBox.information(self, APP_TITLE, "この操作はローカルファイル選択から利用できます。")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.context.shutdown()
        super().closeEvent(event)
