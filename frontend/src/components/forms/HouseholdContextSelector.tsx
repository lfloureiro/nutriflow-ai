import { styles } from "../styles";
import type { Household } from "../types";

type Props = {
  households: Household[];
  selectedHouseholdId: string;
  onChange: (value: string) => void;
};

export function HouseholdContextSelector({
  households,
  selectedHouseholdId,
  onChange,
}: Props) {
  const selectedHousehold =
    households.find((item) => String(item.id) === selectedHouseholdId) ?? null;

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Agregado ativo</h2>

      {households.length === 0 ? (
        <p style={styles.empty}>Ainda não existem agregados.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gap: "14px",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            alignItems: "start",
          }}
        >
          <div style={styles.form}>
            <select
              style={styles.select}
              value={selectedHouseholdId}
              onChange={(e) => onChange(e.target.value)}
            >
              <option value="">Seleciona um agregado</option>
              {households.map((household) => (
                <option key={household.id} value={household.id}>
                  {household.name}
                </option>
              ))}
            </select>
          </div>

          <div
            style={{
              padding: "14px",
              border: "1px solid #374151",
              borderRadius: "12px",
              background: "#111827",
            }}
          >
            <div>
              <strong>Agregado selecionado:</strong>{" "}
              {selectedHousehold?.name ?? "-"}
            </div>
            <div style={{ marginTop: "8px" }}>
              <strong>Membros:</strong> {selectedHousehold?.members.length ?? 0}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}