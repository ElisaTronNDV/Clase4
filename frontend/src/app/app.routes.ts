import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login' },
  { path: 'oficina' },
  { path: 'taller' },
  { path: 'inventario' },
  { path: 'configuracion' },
];
