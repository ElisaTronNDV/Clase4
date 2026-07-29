import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { ProductoOut, ProductoUpdate } from '../../shared/models/productos.models';
import { ProductoSeleccionadoService } from '../producto-seleccionado.service';

@Component({
  selector: 'app-editar-producto',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './editar-producto.component.html',
})
export class EditarProductoComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly productoSeleccionado = inject(ProductoSeleccionadoService);

  producto: ProductoOut | null = null;
  errorMessage: string | null = null;

  form = this.fb.group({
    material: ['', Validators.required],
    espesor_mm: [null as number | null, [Validators.required, Validators.min(0.01)]],
    largo_mm: [null as number | null, [Validators.required, Validators.min(0.01)]],
    ancho_mm: [null as number | null, [Validators.required, Validators.min(0.01)]],
    stock_fisico: [null as number | null, [Validators.required, Validators.min(0)]],
    punto_pedido: [null as number | null, [Validators.required, Validators.min(0)]],
  });

  ngOnInit(): void {
    const producto = this.productoSeleccionado.get();
    if (!producto) {
      this.router.navigate(['/inventario/listado']);
      return;
    }
    this.producto = producto;
    this.form.patchValue({
      material: producto.material,
      espesor_mm: producto.espesor_mm,
      largo_mm: producto.largo_mm,
      ancho_mm: producto.ancho_mm,
      stock_fisico: producto.stock_fisico,
      punto_pedido: producto.punto_pedido,
    });
  }

  submit(): void {
    if (this.form.invalid || !this.producto) {
      return;
    }
    this.errorMessage = null;
    const datos = this.form.getRawValue() as ProductoUpdate;
    this.api.put<ProductoOut>(`/api/productos/${this.producto.id}`, datos).subscribe({
      next: () => {
        this.productoSeleccionado.clear();
        this.router.navigate(['/inventario/listado']);
      },
      error: (err) => {
        this.errorMessage =
          err.status === 409
            ? 'Ya existe otro producto con exactamente el mismo material, espesor y dimensiones.'
            : 'No se pudo guardar la edición. Verificá los datos ingresados.';
      },
    });
  }
}
