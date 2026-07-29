import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../shared/services/api.service';
import { ProductoCreate, ProductoOut } from '../../shared/models/productos.models';

@Component({
  selector: 'app-alta-producto',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './alta-producto.component.html',
})
export class AltaProductoComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  form = this.fb.group({
    material: ['', Validators.required],
    espesor_mm: [null as number | null, [Validators.required, Validators.min(0.01)]],
    largo_mm: [null as number | null, [Validators.required, Validators.min(0.01)]],
    ancho_mm: [null as number | null, [Validators.required, Validators.min(0.01)]],
    stock_fisico: [null as number | null, [Validators.required, Validators.min(0)]],
    punto_pedido: [null as number | null, [Validators.required, Validators.min(0)]],
  });

  errorMessage: string | null = null;

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.errorMessage = null;
    const datos = this.form.getRawValue() as ProductoCreate;
    this.api.post<ProductoOut>('/api/productos', datos).subscribe({
      next: () => {
        this.router.navigate(['/inventario/listado']);
      },
      error: (err) => {
        this.errorMessage =
          err.status === 409
            ? 'Ya existe un producto con exactamente el mismo material, espesor y dimensiones.'
            : 'No se pudo dar de alta el producto. Verificá los datos ingresados.';
      },
    });
  }
}
