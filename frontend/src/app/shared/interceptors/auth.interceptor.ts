import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const TOKEN_STORAGE_KEY = 'dyp_access_token';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  const authReq = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authReq).pipe(
    catchError((error) => {
      if (error.status === 401) {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};
