import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { ProductoOut } from '../../shared/models/productos.models';
import { ProductoSeleccionadoService } from '../producto-seleccionado.service';

@Component({
  selector: 'app-listado-productos',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './listado-productos.component.html',
})
export class ListadoProductosComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly productoSeleccionado = inject(ProductoSeleccionadoService);

  productos: ProductoOut[] = [];
  cargando = false;
  errorMessage: string | null = null;

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.errorMessage = null;
    this.api.get<ProductoOut[]>('/api/productos').subscribe({
      next: (productos) => {
        this.cargando = false;
        this.productos = productos;
      },
      error: () => {
        this.cargando = false;
        this.errorMessage = 'No se pudo obtener el listado de productos.';
      },
    });
  }

  editar(producto: ProductoOut): void {
    this.productoSeleccionado.set(producto);
    this.router.navigate(['/inventario/editar', producto.id]);
  }
}
