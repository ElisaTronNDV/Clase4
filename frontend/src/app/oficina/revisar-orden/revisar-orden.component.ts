import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { OrdenOut } from '../../shared/models/ordenes.models';
import { PropuestaEnEdicionService } from '../propuesta-en-edicion.service';

@Component({
  selector: 'app-revisar-orden',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './revisar-orden.component.html',
})
export class RevisarOrdenComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly propuestaEnEdicion = inject(PropuestaEnEdicionService);
  private readonly router = inject(Router);

  form = this.fb.group({
    multiplicidad: [1, [Validators.required, Validators.min(1)]],
    espesor_mm: [0, [Validators.required, Validators.min(0.01)]],
    material: ['', [Validators.required]],
    largo_mm: [0, [Validators.required, Validators.min(0.01)]],
    ancho_mm: [0, [Validators.required, Validators.min(0.01)]],
    tiempo_ejecucion_estimado: ['', [Validators.required]],
    piezas: this.fb.array([]),
    recortes: this.fb.array([]),
  });

  errorMessage: string | null = null;
  advertenciaProductoInexistente = false;
  enviando = false;

  get piezas(): FormArray {
    return this.form.get('piezas') as FormArray;
  }

  get recortes(): FormArray {
    return this.form.get('recortes') as FormArray;
  }

  ngOnInit(): void {
    const propuesta = this.propuestaEnEdicion.get();
    if (!propuesta) {
      this.router.navigate(['/oficina/subir']);
      return;
    }

    this.form.patchValue({
      multiplicidad: propuesta.multiplicidad ?? 1,
      espesor_mm: propuesta.espesor_mm ?? 0,
      material: propuesta.material ?? '',
      largo_mm: propuesta.largo_mm ?? 0,
      ancho_mm: propuesta.ancho_mm ?? 0,
      tiempo_ejecucion_estimado: propuesta.tiempo_ejecucion_estimado ?? '',
    });

    propuesta.piezas.forEach((pieza) => this.agregarPieza(pieza.descripcion, pieza.cantidad));
    propuesta.recortes.forEach((recorte) =>
      this.agregarRecorte(recorte.largo_mm, recorte.ancho_mm)
    );
  }

  agregarPieza(descripcion = '', cantidad = 1): void {
    this.piezas.push(
      this.fb.group({
        descripcion: [descripcion, Validators.required],
        cantidad: [cantidad, [Validators.required, Validators.min(1)]],
      })
    );
  }

  eliminarPieza(index: number): void {
    this.piezas.removeAt(index);
  }

  agregarRecorte(largo: number | null = null, ancho: number | null = null): void {
    this.recortes.push(
      this.fb.group({
        largo_mm: [largo, [Validators.required, Validators.min(0.01)]],
        ancho_mm: [ancho, [Validators.required, Validators.min(0.01)]],
      })
    );
  }

  eliminarRecorte(index: number): void {
    this.recortes.removeAt(index);
  }

  confirmar(confirmarCreacionAutomatica = false): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.enviando = true;
    this.errorMessage = null;
    this.advertenciaProductoInexistente = false;

    const payload = {
      ...this.form.getRawValue(),
      confirmar_creacion_automatica: confirmarCreacionAutomatica,
    };

    this.api.post<OrdenOut>('/api/ordenes', payload).subscribe({
      next: (orden) => {
        this.enviando = false;
        this.propuestaEnEdicion.clear();
        this.router.navigate(['/oficina/impresion', orden.id]);
      },
      error: (err) => {
        this.enviando = false;
        if (err.status === 404 && err.error?.detail?.advertencia_producto_inexistente) {
          this.advertenciaProductoInexistente = true;
          this.errorMessage = err.error.detail.mensaje ?? 'No existe un producto coincidente.';
        } else if (err.status === 422) {
          this.errorMessage = 'Revisá los datos: hay campos incompletos o inválidos.';
        } else {
          this.errorMessage = 'No se pudo confirmar la orden.';
        }
      },
    });
  }
}
