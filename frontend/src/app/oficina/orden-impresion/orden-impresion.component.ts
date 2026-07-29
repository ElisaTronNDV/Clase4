import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
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
    const id = Number(this.route.snapshot.paramMap.get('id'));
    const orden = this.ordenConfirmada.get();

    if (!orden || orden.id !== id) {
      this.router.navigate(['/oficina/listado']);
      return;
    }
    this.orden = orden;

    this.api.getBlob(`/api/ordenes/${id}/codigo-barras`).subscribe({
      next: (blob) => {
        this.codigoBarrasUrl = URL.createObjectURL(blob);
      },
      error: () => {
        this.errorMessage = 'No se pudo generar el código de barras.';
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
}
