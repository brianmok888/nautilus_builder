export const ValidationPanel = ({ errors }: { errors: string[] }) => {
  if (errors.length === 0) {
    return (
      <p>
        <span className="status-badge">Validation</span> ready for backend
        checks
      </p>
    );
  }

  return (
    <aside className="panel" aria-label="inline validation errors">
      <h3>Validation feedback</h3>
      <ul>
        {errors.map((error) => (
          <li key={error}>{error}</li>
        ))}
      </ul>
    </aside>
  );
};
