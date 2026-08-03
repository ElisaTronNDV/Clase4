import { Injectable, signal } from '@angular/core';

import { PropuestaExtraccion } from '../shared/models/ordenes.models';

@Injectable({ providedIn: 'root' })
export class PropuestaEnEdicionService {
  private readonly propuestas = signal<PropuestaExtraccion[] | null>(null);

  set(propuestas: PropuestaExtraccion[]): void {
    this.propuestas.set(propuestas);
  }

  get(): PropuestaExtraccion[] | null {
    return this.propuestas();
  }

  clear(): void {
    this.propuestas.set(null);
  }
}
