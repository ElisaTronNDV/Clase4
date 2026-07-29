import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { BarcodeFormat } from '@zxing/library';
import { ZXingScannerModule } from '@zxing/ngx-scanner';

import { ApiService } from '../../shared/services/api.service';
import { OrdenDetalle } from '../../shared/models/ordenes.models';
import { OrdenEncontradaService } from '../orden-encontrada.service';

@Component({
  selector: 'app-escanear-orden',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ZXingScannerModule],
  templateUrl: './escanear-orden.component.html',
})
export class EscanearOrdenComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly ordenEncontrada = inject(OrdenEncontradaService);
  private readonly router = inject(Router);

  readonly formatosPermitidos = [BarcodeFormat.CODE_128];

  form = this.fb.group({
    codigoNest: ['', [Validators.required]],
  });

  escaneando = true;
  buscando = false;
  errorMessage: string | null = null;

  onScanSuccess(codigoNest: string): void {
    this.escaneando = false;
    this.buscar(codigoNest);
  }

  onScanError(): void {
    this.errorMessage = 'No se pudo acceder a la cámara. Ingresá el código NEST manualmente.';
  }

  buscarManual(): void {
    if (this.form.invalid) {
      return;
    }
    const codigoNest = (this.form.getRawValue().codigoNest ?? '').trim();
    if (!codigoNest) {
      return;
    }
    this.buscar(codigoNest);
  }

  private buscar(codigoNest: string): void {
    this.buscando = true;
    this.errorMessage = null;
    this.api.get<OrdenDetalle>('/api/ordenes/buscar', { codigo_nest: codigoNest }).subscribe({
      next: (orden) => {
        this.buscando = false;
        this.ordenEncontrada.set(orden);
        this.router.navigate(['/taller/cerrar']);
      },
      error: (err) => {
        this.buscando = false;
        this.errorMessage =
          err.status === 404
            ? `No existe ninguna orden con el código "${codigoNest}".`
            : 'No se pudo buscar la orden.';
      },
    });
  }
}
