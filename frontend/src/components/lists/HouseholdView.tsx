import { styles } from "../styles";
import type { Household } from "../types";

type Props = {
  households: Household[];
};

export function HouseholdView({ households }: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Agregados e membros</h2>

      {households.length === 0 ? (
        <p style={styles.empty}>Sem agregados.</p>
      ) : (
        <ul style={styles.list}>
          {households.map((household) => (
            <li key={household.id} style={styles.listItem}>
              <strong>{household.name}</strong>

              {household.members.length === 0 ? (
                <p style={styles.empty}>Sem membros.</p>
              ) : (
                <ul style={styles.sourceList}>
                  {household.members.map((member) => (
                    <li key={member.id} style={styles.sourceItem}>
                      {member.name}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}