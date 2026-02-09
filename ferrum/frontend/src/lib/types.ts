export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  org_id: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  tier?: string;
  created_at: string;
}

export interface Supplier {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  cage_code?: string;
  sam_uei?: string;
  duns_number?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  naics_codes?: string[];
  website?: string;
  contact_email?: string;
  contact_phone?: string;
  small_business: boolean;
  woman_owned: boolean;
  veteran_owned: boolean;
  hub_zone: boolean;
  risk_score?: number;
  contains_cui: boolean;
  created_at: string;
  updated_at: string;
  capabilities?: SupplierCapability[];
  certifications?: SupplierCertification[];
  materials?: SupplierMaterial[];
}

export interface SupplierCapability {
  id: string;
  name: string;
  category?: string;
  proficiency?: string;
}

export interface SupplierCertification {
  id: string;
  name: string;
  body?: string;
  cert_number?: string;
  issued_date?: string;
  expiry_date?: string;
  status?: string;
}

export interface SupplierMaterial {
  id: string;
  name: string;
  specification?: string;
}

export interface Material {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  category_id?: string;
  specification?: string;
  grade?: string;
  form?: string;
  material_type?: string;
  nsn?: string;
  specialty_metal: boolean;
  domestic_required: boolean;
  export_controlled: boolean;
  created_at: string;
  updated_at: string;
  suppliers?: MaterialSupplier[];
}

export interface MaterialSupplier {
  id: string;
  name: string;
  cage_code?: string;
}

export interface MaterialCategory {
  id: string;
  name: string;
  slug: string;
  parent_id?: string;
}

export interface Price {
  id: string;
  supplier_id: string;
  material_id: string;
  unit_price: number;
  currency: string;
  minimum_order_quantity?: number;
  lead_time_days?: number;
  valid_from?: string;
  valid_until?: string;
}

export interface ComplianceRecord {
  id: string;
  supplier_id: string;
  regulation: string;
  status: 'compliant' | 'non_compliant' | 'pending' | 'not_applicable';
  last_audit_date?: string;
  next_audit_date?: string;
  notes?: string;
}

export interface SearchResponse {
  results: Record<string, any>[];
  query_interpretation: string;
  total: number;
  facets?: Record<string, any>;
  search_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
