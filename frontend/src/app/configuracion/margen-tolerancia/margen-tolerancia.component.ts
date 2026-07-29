import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../shared/services/api.service';
import { ConfiguracionOut, ConfiguracionUpdate } from '../../shared/models/configuracion.models';

@Component({
  selector: 'app-margen-tolerancia',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './margen-tolerancia.component.html',
})
export class MargenToleranciaComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);

  form = this.fb.group({
    margen_tolerancia_mm: [null as number | null, [Validators.required, Validators.min(0.001)]],
  });

  cargando = false;
  guardando = false;
  errorMessage: string | null = null;
  guardadoOk = false;

  ngOnInit(): void {
    this.cargando = true;
    this.api.get<ConfiguracionOut>('/api/configuracion').subscribe({
      next: (configuracion) => {
        this.cargando = false;
        this.form.patchValue({ margen_tolerancia_mm: configuracion.margen_tolerancia_mm });
      },
      error: () => {
        this.cargando = false;
        this.errorMessage = 'No se pudo obtener el margen de tolerancia actual.';
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      return;
    }
    this.errorMessage = null;
    this.guardadoOk = false;
    this.guardando = true;
    const datos = this.form.getRawValue() as ConfiguracionUpdate;
    this.api.put<ConfiguracionOut>('/api/configuracion', datos).subscribe({
      next: (configuracion) => {
        this.guardando = false;
        this.guardadoOk = true;
        this.form.patchValue({ margen_tolerancia_mm: configuracion.margen_tolerancia_mm });
      },
      error: () => {
        this.guardando = false;
        this.errorMessage = 'El margen debe ser un valor mayor a cero.';
      },
    });
  }
}
