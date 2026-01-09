/**
 * TREXIMA v4.0 - 404 Not Found Page
 */

import { Link } from 'react-router-dom';
import { Home, AlertTriangle } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full text-center">
        <AlertTriangle className="mx-auto h-16 w-16 text-sap-orange-500" />

        <h1 className="mt-6 text-6xl font-extrabold text-gray-900">404</h1>

        <p className="mt-4 text-xl text-gray-600">Page not found</p>

        <p className="mt-2 text-sm text-gray-500">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="mt-8">
          <Link to="/" className="btn-primary">
            <Home className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
