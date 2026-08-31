// Vraća poruku greške ili null ako je polje validno

export function validateRequired(value: string, fieldName: string): string | null {
  if (!value || value.trim() === "") {
    return `${fieldName} je obavezno polje`;
  }
  return null;
}

export function validateJMBG(jmbg: string): string | null {
  if (!jmbg) return "JMBG je obavezan";
  if (!/^\d{13}$/.test(jmbg)) {
    return "JMBG mora imati tačno 13 cifara";
  }
  return null;
}

export function validateEmail(email: string): string | null {
  if (!email) return "Email je obavezan";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return "Email nije u ispravnom formatu";
  }
  return null;
}

export function validatePassword(password: string): string | null {
  if (!password) return "Lozinka je obavezna";
  if (password.length < 6) {
    return "Lozinka mora imati najmanje 6 karaktera";
  }
  return null;
}

// Sakuplja sve greške forme, vraća prvu ili null
export function firstError(...validations: (string | null)[]): string | null {
  return validations.find((v) => v !== null) || null;
}