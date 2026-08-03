import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { OrdenOut } from '../../shared/models/ordenes.models';
import { OrdenConfirmadaService, OrdenParaImprimir } from '../orden-confirmada.service';
import { PropuestaEnEdicionService } from '../propuesta-en-edicion.service';

interface EstadoOrden {
  error: string | null;
  advertencia: boolean;
}

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
  private readonly ordenConfirmada = inject(OrdenConfirmadaService);
  private readonly router = inject(Router);

  ordenesForm = this.fb.array<FormGroup>([]);
  estados: EstadoOrden[] = [];
  confirmadas: boolean[] = [];
  tabActiva = 0;
  enviando = false;

  private ordenesConfirmadas: OrdenParaImprimir[] = [];

  ngOnInit(): void {
    const propuestas = this.propuestaEnEdicion.get();
    if (!propuestas || propuestas.length === 0) {
      this.router.navigate(['/oficina/subir']);
      return;
    }

    propuestas.forEach((propuesta) => {
      const grupo = this.crearGrupoOrden();
      grupo.patchValue({
        multiplicidad: propuesta.multiplicidad ?? 1,
        espesor_mm: propuesta.espesor_mm ?? 0,
        material: propuesta.material ?? '',
        largo_mm: propuesta.largo_mm ?? 0,
        ancho_mm: propuesta.ancho_mm ?? 0,
        tiempo_ejecucion_estimado: propuesta.tiempo_ejecucion_estimado ?? '',
      });

      const piezas = grupo.get('piezas') as FormArray;
      propuesta.piezas.forEach((pieza) =>
        piezas.push(this.crearControlPieza(pieza.descripcion, pieza.cantidad))
      );

      const recortes = grupo.get('recortes') as FormArray;
      propuesta.recortes.forEach((recorte) =>
        recortes.push(this.crearControlRecorte(recorte.largo_mm, recorte.ancho_mm))
      );

      this.ordenesForm.push(grupo);
      this.estados.push({ error: null, advertencia: false });
      this.confirmadas.push(false);
    });
  }

  grupoDe(indice: number): FormGroup {
    return this.ordenesForm.at(indice) as FormGroup;
  }

  piezasDe(indice: number): FormArray {
    return this.grupoDe(indice).get('piezas') as FormArray;
  }

  recortesDe(indice: number): FormArray {
    return this.grupoDe(indice).get('recortes') as FormArray;
  }

  agregarPieza(indice: number): void {
    this.piezasDe(indice).push(this.crearControlPieza());
  }

  eliminarPieza(indice: number, indicePieza: number): void {
    this.piezasDe(indice).removeAt(indicePieza);
  }

  agregarRecorte(indice: number): void {
    this.recortesDe(indice).push(this.crearControlRecorte());
  }

  eliminarRecorte(indice: number, indiceRecorte: number): void {
    this.recortesDe(indice).removeAt(indiceRecorte);
  }

  cancelar(): void {
    this.propuestaEnEdicion.clear();
    this.router.navigate(['/oficina/subir']);
  }

  confirmarTodas(): void {
    this.ordenesConfirmadas = [];
    this.confirmarDesde(0);
  }

  confirmarConCreacionAutomatica(indice: number): void {
    this.enviarOrden(indice, true);
  }

  private confirmarDesde(indice: number): void {
    if (indice >= this.ordenesForm.length) {
      this.propuestaEnEdicion.clear();
      if (this.ordenesConfirmadas.length === 1) {
        const [orden] = this.ordenesConfirmadas;
        this.ordenConfirmada.set(orden);
        this.router.navigate(['/oficina/impresion', orden.codigo_nest]);
      } else {
        this.router.navigate(['/oficina/listado']);
      }
      return;
    }

    this.tabActiva = indice;
    const grupo = this.grupoDe(indice);
    if (grupo.invalid) {
      grupo.markAllAsTouched();
      return;
    }

    this.enviarOrden(indice, false);
  }

  private enviarOrden(indice: number, confirmarCreacionAutomatica: boolean): void {
    this.tabActiva = indice;
    this.enviando = true;
    this.estados[indice] = { error: null, advertencia: false };

    const grupo = this.grupoDe(indice);
    const payload = {
      ...grupo.getRawValue(),
      confirmar_creacion_automatica: confirmarCreacionAutomatica,
    };

    this.api.post<OrdenOut>('/api/ordenes', payload).subscribe({
      next: (orden) => {
        this.enviando = false;
        this.confirmadas[indice] = true;
        const { material, espesor_mm, largo_mm, ancho_mm } = grupo.getRawValue();
        this.ordenesConfirmadas.push({
          id: orden.id,
          codigo_nest: orden.codigo_nest,
          material: material ?? '',
          espesor_mm: espesor_mm ?? 0,
          largo_mm: largo_mm ?? 0,
          ancho_mm: ancho_mm ?? 0,
          piezas: this.piezasDe(indice).getRawValue(),
        });
        this.confirmarDesde(indice + 1);
      },
      error: (err) => {
        this.enviando = false;
        if (err.status === 404 && err.error?.detail?.advertencia_producto_inexistente) {
          this.estados[indice] = {
            advertencia: true,
            error: err.error.detail.mensaje ?? 'No existe un producto coincidente.',
          };
        } else if (err.status === 422) {
          this.estados[indice] = {
            advertencia: false,
            error: 'Revisá los datos: hay campos incompletos o inválidos.',
          };
        } else {
          this.estados[indice] = { advertencia: false, error: 'No se pudo confirmar la orden.' };
        }
      },
    });
  }

  private crearGrupoOrden(): FormGroup {
    return this.fb.group({
      multiplicidad: [1, [Validators.required, Validators.min(1)]],
      espesor_mm: [0, [Validators.required, Validators.min(0.01)]],
      material: ['', [Validators.required]],
      largo_mm: [0, [Validators.required, Validators.min(0.01)]],
      ancho_mm: [0, [Validators.required, Validators.min(0.01)]],
      tiempo_ejecucion_estimado: ['', [Validators.required]],
      piezas: this.fb.array([]),
      recortes: this.fb.array([]),
    });
  }

  private crearControlPieza(descripcion = '', cantidad = 1): FormGroup {
    return this.fb.group({
      descripcion: [descripcion, Validators.required],
      cantidad: [cantidad, [Validators.required, Validators.min(1)]],
    });
  }

  private crearControlRecorte(largo: number | null = null, ancho: number | null = null): FormGroup {
    return this.fb.group({
      largo_mm: [largo, [Validators.required, Validators.min(0.01)]],
      ancho_mm: [ancho, [Validators.required, Validators.min(0.01)]],
    });
  }
}
