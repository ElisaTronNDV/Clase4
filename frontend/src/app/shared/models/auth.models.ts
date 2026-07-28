export interface UsuarioCreate {
  email: string;
  password: string;
}

export interface UsuarioLogin {
  email: string;
  password: string;
}

export interface UsuarioOut {
  id: number;
  email: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_at: string;
}
