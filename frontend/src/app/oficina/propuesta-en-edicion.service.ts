import { Injectable, signal } from '@angular/core';

import { PropuestaExtraccion } from '../shared/models/ordenes.models';

@Injectable({ providedIn: 'root' })
export class PropuestaEnEdicionService {
  private readonly propuesta = signal<PropuestaExtraccion | null>(null);

  set(propuesta: PropuestaExtraccion): void {
    this.propuesta.set(propuesta);
  }

  get(): PropuestaExtraccion | null {
    return this.propuesta();
  }

  clear(): void {
    this.propuesta.set(null);
  }
}
