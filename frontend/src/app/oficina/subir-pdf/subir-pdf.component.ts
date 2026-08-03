import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { ApiService } from '../../shared/services/api.service';
import { PropuestaExtraccion } from '../../shared/models/ordenes.models';
import { PropuestaEnEdicionService } from '../propuesta-en-edicion.service';

const TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024;

@Component({
  selector: 'app-subir-pdf',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './subir-pdf.component.html',
})
export class SubirPdfComponent {
  private readonly api = inject(ApiService);
  private readonly propuestaEnEdicion = inject(PropuestaEnEdicionService);
  private readonly router = inject(Router);

  private subidaEnCurso: Subscription | null = null;

  enviando = false;
  errorMessage: string | null = null;

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0] ?? null;
    input.value = '';

    if (!archivo) {
      return;
    }

    this.errorMessage = null;

    if (archivo.type !== 'application/pdf') {
      this.errorMessage = 'El archivo debe ser un PDF válido.';
      return;
    }
    if (archivo.size > TAMANO_MAXIMO_BYTES) {
      this.errorMessage = 'El archivo supera el tamaño máximo permitido de 20 MB.';
      return;
    }

    this.subir(archivo);
  }

  cancelar(): void {
    this.subidaEnCurso?.unsubscribe();
    this.subidaEnCurso = null;
    this.enviando = false;
    this.errorMessage = null;
  }

  private subir(archivo: File): void {
    const formData = new FormData();
    formData.append('archivo', archivo);

    this.enviando = true;
    this.subidaEnCurso = this.api
      .post<PropuestaExtraccion[]>('/api/ordenes/extraer-pdf', formData)
      .subscribe({
        next: (propuestas) => {
          this.enviando = false;
          this.propuestaEnEdicion.set(propuestas);
          this.router.navigate(['/oficina/revisar']);
        },
        error: (err) => {
          this.enviando = false;
          if (err.status === 413) {
            this.errorMessage = 'El archivo supera el tamaño máximo permitido de 20 MB.';
          } else if (err.status === 400) {
            this.errorMessage = 'El archivo debe ser un PDF válido.';
          } else {
            this.errorMessage = 'No se pudo procesar el archivo de corte.';
          }
        },
      });
  }
}
