import { KeyRound, Save } from "lucide-react";
import { useEffect, useState } from "react";

import type { LLMFeatureProfile, RuntimeSettingsPublic } from "../../shared/types/api";

interface SettingsViewProps {
  settings: RuntimeSettingsPublic;
  onSessionKey: (apiKey: string) => void;
  onPersistKey: (apiKey: string) => void;
  onResponseStorage: (mode: "normal" | "privacy") => void;
  onProfiles: (profiles: Record<string, LLMFeatureProfile>) => void;
  onConnectionTest: () => void;
}

export function SettingsView({
  settings,
  onSessionKey,
  onPersistKey,
  onResponseStorage,
  onProfiles,
  onConnectionTest
}: SettingsViewProps) {
  const [apiKey, setApiKey] = useState("");
  const [profiles, setProfiles] = useState(settings.feature_profiles);
  const [responseStorage, setResponseStorage] = useState(settings.response_storage);

  useEffect(() => {
    setProfiles(settings.feature_profiles);
  }, [settings.feature_profiles]);

  useEffect(() => {
    setResponseStorage(settings.response_storage);
  }, [settings.response_storage]);

  const updateProfile = (
    featureId: string,
    field: keyof LLMFeatureProfile,
    value: string
  ) => {
    setProfiles({
      ...profiles,
      [featureId]: { ...profiles[featureId], [field]: value }
    });
  };

  return (
    <section className="workspace-pane" aria-label="Settings">
      <div className="section-header">
        <h1>Settings</h1>
        <button type="button" onClick={() => onProfiles(profiles)}>
          <Save size={16} /> Profiles 保存
        </button>
      </div>

      <section className="plain-panel">
        <h2>API Key</h2>
        <div className="inline-form">
          <input
            type="password"
            value={apiKey}
            autoComplete="off"
            onChange={(event) => setApiKey(event.currentTarget.value)}
          />
          <button type="button" className="secondary" onClick={() => onSessionKey(apiKey)}>
            <KeyRound size={16} /> Session
          </button>
          <button type="button" onClick={() => onPersistKey(apiKey)}>
            <KeyRound size={16} /> Keyring
          </button>
          <button type="button" className="secondary" onClick={onConnectionTest}>
            Test
          </button>
        </div>
        <p>{settings.api_key_configured ? "API key configured" : "MockLLM mode"}</p>
      </section>

      <section className="plain-panel">
        <h2>Privacy</h2>
        <label className="switch-row">
          <input
            type="checkbox"
            checked={responseStorage === "privacy"}
            onChange={(event) => {
              const mode = event.currentTarget.checked ? "privacy" : "normal";
              setResponseStorage(mode);
              onResponseStorage(mode);
            }}
          />
          <span>Privacy mode</span>
        </label>
      </section>

      <section className="plain-panel">
        <h2>Generation Service Profile</h2>
        <p>{settings.ruleset.display_name}</p>
      </section>

      <section className="plain-panel">
        <h2>LLM Feature Profiles</h2>
        <div className="profiles-grid">
          {Object.entries(profiles).map(([featureId, profile]) => (
            <article className="profile-row" key={featureId}>
              <strong>{settings.feature_display_names[featureId] ?? featureId}</strong>
              <select
                value={profile.model}
                onChange={(event) => updateProfile(featureId, "model", event.currentTarget.value)}
              >
                {settings.available_models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <select
                value={profile.reasoning_effort}
                onChange={(event) =>
                  updateProfile(featureId, "reasoning_effort", event.currentTarget.value)
                }
              >
                {settings.reasoning_efforts.map((effort) => (
                  <option key={effort} value={effort}>
                    {effort}
                  </option>
                ))}
              </select>
              <select
                value={profile.vocabulary_amount}
                onChange={(event) =>
                  updateProfile(featureId, "vocabulary_amount", event.currentTarget.value)
                }
              >
                {settings.vocabulary_amounts.map((amount) => (
                  <option key={amount} value={amount}>
                    {settings.vocabulary_amount_labels[amount] ?? amount}
                  </option>
                ))}
              </select>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
