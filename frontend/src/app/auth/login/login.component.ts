import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthTokenService } from '../auth-token.service';
import { ApiService } from '../../shared/services/api.service';
import { Token, UsuarioLogin } from '../../shared/models/auth.models';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly tokenService = inject(AuthTokenService);
  private readonly router = inject(Router);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  errorMessage: string | null = null;

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.errorMessage = null;
    const credenciales = this.form.getRawValue() as UsuarioLogin;
    this.api.post<Token>('/api/auth/login', credenciales).subscribe({
      next: (token) => {
        this.tokenService.setToken(token.access_token);
        this.router.navigate(['/oficina']);
      },
      error: () => {
        this.errorMessage = 'Email o contraseña inválidos.';
      },
    });
  }
}
