import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

export const API_BASE_URL = 'http://localhost:8000';

@Injectable({ providedIn: 'root' })
export class ApiService {
  readonly baseUrl = API_BASE_URL;

  constructor(private readonly http: HttpClient) {}

  get<T>(path: string, params?: Record<string, string>) {
    return this.http.get<T>(`${this.baseUrl}${path}`, { params });
  }

  post<T>(path: string, body: unknown) {
    return this.http.post<T>(`${this.baseUrl}${path}`, body);
  }

  put<T>(path: string, body: unknown) {
    return this.http.put<T>(`${this.baseUrl}${path}`, body);
  }
}
