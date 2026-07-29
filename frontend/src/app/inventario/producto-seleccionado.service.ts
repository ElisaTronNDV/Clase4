import { Injectable, signal } from '@angular/core';

import { ProductoOut } from '../shared/models/productos.models';

@Injectable({ providedIn: 'root' })
export class ProductoSeleccionadoService {
  private readonly producto = signal<ProductoOut | null>(null);

  set(producto: ProductoOut): void {
    this.producto.set(producto);
  }

  get(): ProductoOut | null {
    return this.producto();
  }

  clear(): void {
    this.producto.set(null);
  }
}
