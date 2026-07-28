import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { UsuarioCreate, UsuarioOut } from '../../shared/models/auth.models';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './registro.component.html',
})
export class RegistroComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  errorMessage: string | null = null;

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.errorMessage = null;
    const datos = this.form.getRawValue() as UsuarioCreate;
    this.api.post<UsuarioOut>('/api/auth/registro', datos).subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: (err) => {
        this.errorMessage =
          err.status === 409
            ? 'Ese email ya está registrado.'
            : 'No se pudo crear la cuenta. Verificá los datos ingresados.';
      },
    });
  }
}
