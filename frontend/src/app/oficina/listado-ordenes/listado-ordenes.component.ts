import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';

import { ApiService } from '../../shared/services/api.service';
import { OrdenListado } from '../../shared/models/ordenes.models';

@Component({
  selector: 'app-listado-ordenes',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './listado-ordenes.component.html',
})
export class ListadoOrdenesComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);

  filtros = this.fb.group({
    estado: [''],
    nest: [''],
  });

  ordenes: OrdenListado[] = [];
  cargando = false;
  errorMessage: string | null = null;

  ngOnInit(): void {
    this.buscar();
  }

  buscar(): void {
    const { estado, nest } = this.filtros.getRawValue();
    const params: Record<string, string> = {};
    if (estado) {
      params['estado'] = estado;
    }
    if (nest) {
      params['nest'] = nest;
    }

    this.cargando = true;
    this.errorMessage = null;
    this.api.get<OrdenListado[]>('/api/ordenes', params).subscribe({
      next: (ordenes) => {
        this.cargando = false;
        this.ordenes = ordenes;
      },
      error: () => {
        this.cargando = false;
        this.errorMessage = 'No se pudo obtener el listado de órdenes.';
      },
    });
  }

  limpiarFiltros(): void {
    this.filtros.reset({ estado: '', nest: '' });
    this.buscar();
  }
}
