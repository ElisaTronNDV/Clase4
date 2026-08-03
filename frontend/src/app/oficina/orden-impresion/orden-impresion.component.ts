import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { OrdenDetalle } from '../../shared/models/ordenes.models';
import { OrdenConfirmadaService, OrdenParaImprimir } from '../orden-confirmada.service';

@Component({
  selector: 'app-orden-impresion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './orden-impresion.component.html',
})
export class OrdenImpresionComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly api = inject(ApiService);
  private readonly ordenConfirmada = inject(OrdenConfirmadaService);

  orden: OrdenParaImprimir | null = null;
  codigoBarrasUrl: string | null = null;
  errorMessage: string | null = null;

  ngOnInit(): void {
    const codigoNest = this.route.snapshot.paramMap.get('nest') ?? '';
    const cacheada = this.ordenConfirmada.get();

    if (cacheada && cacheada.codigo_nest === codigoNest) {
      this.mostrarOrden(cacheada);
      return;
    }

    this.api.get<OrdenDetalle>('/api/ordenes/buscar', { codigo_nest: codigoNest }).subscribe({
      next: (orden) => {
        this.mostrarOrden({
          id: orden.id,
          codigo_nest: orden.codigo_nest,
          material: orden.material,
          espesor_mm: orden.espesor_mm,
          largo_mm: orden.largo_mm,
          ancho_mm: orden.ancho_mm,
          piezas: orden.piezas,
        });
      },
      error: (err) => {
        if (err.status === 404) {
          this.router.navigate(['/oficina/listado']);
          return;
        }
        this.errorMessage = 'No se pudo obtener la orden a imprimir.';
      },
    });
  }

  ngOnDestroy(): void {
    if (this.codigoBarrasUrl) {
      URL.revokeObjectURL(this.codigoBarrasUrl);
    }
  }

  imprimir(): void {
    window.print();
  }

  volver(): void {
    this.router.navigate(['/oficina/listado']);
  }

  private mostrarOrden(orden: OrdenParaImprimir): void {
    this.orden = orden;
    this.api.getBlob(`/api/ordenes/${orden.id}/codigo-barras`).subscribe({
      next: (blob) => {
        this.codigoBarrasUrl = URL.createObjectURL(blob);
      },
      error: () => {
        this.errorMessage = 'No se pudo generar el código de barras.';
      },
    });
  }
}
