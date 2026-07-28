import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then((m) => m.LoginComponent),
  },
  { path: 'oficina' },
  { path: 'taller' },
  { path: 'inventario' },
  { path: 'configuracion' },
];
