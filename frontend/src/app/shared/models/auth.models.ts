export interface UsuarioLogin {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_at: string;
}
