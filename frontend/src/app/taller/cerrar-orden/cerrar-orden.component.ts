import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { OrdenCerrada, OrdenDetalle } from '../../shared/models/ordenes.models';
import { OrdenEncontradaService } from '../orden-encontrada.service';

@Component({
  selector: 'app-cerrar-orden',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cerrar-orden.component.html',
})
export class CerrarOrdenComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly ordenEncontrada = inject(OrdenEncontradaService);
  private readonly router = inject(Router);

  orden: OrdenDetalle | null = null;
  cerrando = false;
  errorMessage: string | null = null;
  cerrada = false;

  ngOnInit(): void {
    const orden = this.ordenEncontrada.get();
    if (!orden) {
      this.router.navigate(['/taller/escanear']);
      return;
    }
    this.orden = orden;
  }

  finalizar(): void {
    if (!this.orden) {
      return;
    }
    this.cerrando = true;
    this.errorMessage = null;

    // FR-021: sin modo offline ni reintento automático — si falla, se muestra el error
    // y queda bloqueado hasta que el usuario reintente manualmente (con conexión).
    this.api.post<OrdenCerrada>(`/api/ordenes/${this.orden.id}/cerrar`, {}).subscribe({
      next: () => {
        this.cerrando = false;
        this.cerrada = true;
        this.ordenEncontrada.clear();
      },
      error: (err) => {
        this.cerrando = false;
        if (err.status === 409) {
          this.errorMessage = 'La orden ya estaba cerrada.';
        } else if (err.status === 404) {
          this.errorMessage = 'La orden ya no existe.';
        } else {
          this.errorMessage =
            'No se pudo conectar con el servidor para finalizar la orden. Verificá tu ' +
            'conexión e intentá de nuevo.';
        }
      },
    });
  }

  buscarOtra(): void {
    this.ordenEncontrada.clear();
    this.router.navigate(['/taller/escanear']);
  }
}
