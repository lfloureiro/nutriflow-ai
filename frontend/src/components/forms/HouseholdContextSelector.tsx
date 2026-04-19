import { styles } from "../styles";
import type { Household } from "../types";

type Props = {
  households: Household[];
  selectedHouseholdId: string;
  onChange: (value: string) => void;
  isLoading?: boolean;
};

export function HouseholdContextSelector({
  households,
  selectedHouseholdId,
  onChange,
  isLoading = false,
}: Props) {
  const selectedHousehold =
    households.find((item) => String(item.id) === selectedHouseholdId) ?? null;

  return (
    <section style={styles.card}>
      <div className="nf-kicker">Agregado ativo</div>
      <h2 style={styles.sectionTitle}>Contexto de trabalho</h2>

      {households.length === 0 ? (
        <p style={{ ...styles.empty, marginTop: "10px" }}>
          Ainda não existem agregados. Cria um agregado em “Família e preferências”.
        </p>
      ) : (
        <div className="nf-household-grid" style={{ marginTop: "14px" }}>
          <div>
            <label htmlFor="household-selector" className="nf-field-label">
              Agregado selecionado
            </label>

            <select
              id="household-selector"
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

            {isLoading && (
              <p className="nf-inline-note">A atualizar plano e compras…</p>
            )}
          </div>

          <div className="nf-household-summary">
            <div>
              <strong>Agregado:</strong> {selectedHousehold?.name ?? "-"}
            </div>
            <div>
              <strong>Membros:</strong> {selectedHousehold?.members.length ?? 0}
            </div>
            <div>
              <strong>Estado:</strong>{" "}
              {selectedHousehold ? "Ativo" : "Sem agregado selecionado"}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}