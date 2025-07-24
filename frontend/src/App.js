import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetch(`${API}/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data.id) {
          setUser(data);
        } else {
          localStorage.removeItem('token');
          setToken(null);
        }
      })
      .catch(() => {
        localStorage.removeItem('token');
        setToken(null);
      })
      .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const response = await fetch(`${API}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      return { success: true };
    } else {
      const error = await response.json();
      return { success: false, error: error.detail };
    }
  };

  const register = async (userData) => {
    const response = await fetch(`${API}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    
    if (response.ok) {
      return { success: true };
    } else {
      const error = await response.json();
      return { success: false, error: error.detail };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// API Helper
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` })
  };

  const response = await fetch(`${API}${endpoint}`, {
    headers: { ...defaultHeaders, ...options.headers },
    ...options
  });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }

  return response.json();
};

// Components
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">B2B Commerce</h1>
        {user && (
          <div className="flex items-center space-x-4">
            <span className="text-sm">
              {user.company_name} ({user.role})
            </span>
            <button 
              onClick={logout}
              className="bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded text-sm"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(email, password);
    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="email"
                required
                className="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                type="password"
                required
                className="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    company_name: '',
    contact_person: '',
    phone: '',
    role: 'buyer'
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await register(formData);
    if (result.success) {
      setSuccess(true);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full text-center">
          <h2 className="text-2xl font-bold text-green-600 mb-4">Registration Successful!</h2>
          <p className="text-gray-600 mb-4">Your account has been created. You can now sign in.</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <input
              type="email"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Email address"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
            />
            <input
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
            />
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Company Name"
              value={formData.company_name}
              onChange={(e) => setFormData({...formData, company_name: e.target.value})}
            />
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Contact Person"
              value={formData.contact_person}
              onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
            />
            <input
              type="tel"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Phone Number"
              value={formData.phone}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
            />
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="buyer">Buyer</option>
              <option value="supplier">Supplier</option>
            </select>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiCall('/dashboard/stats')
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center">Loading dashboard...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">
        Welcome, {user.contact_person}
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {user.role === 'admin' && (
          <>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">Total Users</h3>
              <p className="text-3xl font-bold text-blue-600">{stats.total_users || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">Total Products</h3>
              <p className="text-3xl font-bold text-green-600">{stats.total_products || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">Total Orders</h3>
              <p className="text-3xl font-bold text-purple-600">{stats.total_orders || 0}</p>
            </div>
          </>
        )}
        
        {user.role === 'supplier' && (
          <>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">My Products</h3>
              <p className="text-3xl font-bold text-blue-600">{stats.my_products || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">My Orders</h3>
              <p className="text-3xl font-bold text-green-600">{stats.my_orders || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">Pending RFQs</h3>
              <p className="text-3xl font-bold text-orange-600">{stats.pending_rfqs || 0}</p>
            </div>
          </>
        )}
        
        {user.role === 'buyer' && (
          <>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">My RFQs</h3>
              <p className="text-3xl font-bold text-blue-600">{stats.my_rfqs || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-700">My Orders</h3>
              <p className="text-3xl font-bold text-green-600">{stats.my_orders || 0}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    Promise.all([
      apiCall('/products'),
      apiCall('/categories')
    ])
    .then(([productsData, categoriesData]) => {
      setProducts(productsData);
      setCategories(categoriesData);
    })
    .catch(console.error)
    .finally(() => setLoading(false));
  }, []);

  const createRFQ = async (productId) => {
    const quantity = prompt('Enter quantity needed:');
    const message = prompt('Add a message (optional):') || '';
    
    if (quantity && quantity > 0) {
      try {
        await apiCall('/rfqs', {
          method: 'POST',
          body: JSON.stringify({
            product_id: productId,
            quantity: parseInt(quantity),
            message,
            expires_in_days: 7
          })
        });
        alert('RFQ created successfully!');
      } catch (error) {
        alert('Failed to create RFQ: ' + error.message);
      }
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading products...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Products</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map(product => {
          const category = categories.find(c => c.id === product.category_id);
          return (
            <div key={product.id} className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-2">{product.name}</h3>
              <p className="text-gray-600 mb-2">{product.description}</p>
              <p className="text-sm text-gray-500 mb-2">
                Category: {category?.name || 'Unknown'}
              </p>
              <p className="text-lg font-bold text-green-600 mb-2">
                ${product.price}/unit
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Stock: {product.stock_quantity} | Min Order: {product.min_order_quantity}
              </p>
              
              {user.role === 'buyer' && (
                <button
                  onClick={() => createRFQ(product.id)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded"
                >
                  Request Quote
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const RFQList = () => {
  const [rfqs, setRfqs] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    Promise.all([
      apiCall('/rfqs'),
      apiCall('/products')
    ])
    .then(([rfqData, productData]) => {
      setRfqs(rfqData);
      setProducts(productData);
    })
    .catch(console.error)
    .finally(() => setLoading(false));
  }, []);

  const submitQuote = async (rfqId) => {
    const pricePerUnit = prompt('Enter your price per unit:');
    const deliveryTime = prompt('Enter delivery time:');
    const message = prompt('Add a message (optional):') || '';
    
    if (pricePerUnit && deliveryTime) {
      try {
        await apiCall('/quotes', {
          method: 'POST',
          body: JSON.stringify({
            rfq_id: rfqId,
            price_per_unit: parseFloat(pricePerUnit),
            delivery_time: deliveryTime,
            message
          })
        });
        alert('Quote submitted successfully!');
        // Refresh RFQs
        window.location.reload();
      } catch (error) {
        alert('Failed to submit quote: ' + error.message);
      }
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading RFQs...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">
        {user.role === 'buyer' ? 'My RFQs' : 'Available RFQs'}
      </h1>
      
      <div className="grid grid-cols-1 gap-6">
        {rfqs.map(rfq => {
          const product = products.find(p => p.id === rfq.product_id);
          return (
            <div key={rfq.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold">
                    {product?.name || 'Product Not Found'}
                  </h3>
                  <p className="text-gray-600">Quantity: {rfq.quantity}</p>
                  <p className="text-sm text-gray-500">
                    Expires: {new Date(rfq.expires_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  rfq.status === 'open' ? 'bg-green-100 text-green-800' :
                  rfq.status === 'quoted' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {rfq.status}
                </span>
              </div>
              
              {rfq.message && (
                <p className="text-gray-700 mb-4">Message: {rfq.message}</p>
              )}
              
              {user.role === 'supplier' && rfq.status === 'open' && (
                <button
                  onClick={() => submitQuote(rfq.id)}
                  className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded"
                >
                  Submit Quote
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Navigation = () => {
  const { user } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');

  const navItems = [
    { key: 'dashboard', label: 'Dashboard', roles: ['admin', 'supplier', 'buyer'] },
    { key: 'products', label: 'Products', roles: ['admin', 'supplier', 'buyer'] },
    { key: 'rfqs', label: 'RFQs', roles: ['supplier', 'buyer'] },
    { key: 'orders', label: 'Orders', roles: ['admin', 'supplier', 'buyer'] }
  ];

  const filteredNavItems = navItems.filter(item => item.roles.includes(user.role));

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'products':
        return <ProductList />;
      case 'rfqs':
        return <RFQList />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <nav className="w-64 bg-white shadow-lg">
        <div className="p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Navigation</h2>
          <ul className="space-y-2">
            {filteredNavItems.map(item => (
              <li key={item.key}>
                <button
                  onClick={() => setCurrentView(item.key)}
                  className={`w-full text-left px-4 py-2 rounded hover:bg-blue-50 ${
                    currentView === item.key ? 'bg-blue-100 text-blue-600' : 'text-gray-700'
                  }`}
                >
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </nav>
      
      <main className="flex-1 overflow-auto">
        {renderContent()}
      </main>
    </div>
  );
};

const MainApp = () => {
  const { user, loading } = useAuth();
  const [showRegister, setShowRegister] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (user) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <Navigation />
      </div>
    );
  }

  return (
    <div>
      {showRegister ? (
        <div>
          <RegisterForm />
          <div className="text-center mt-4">
            <button
              onClick={() => setShowRegister(false)}
              className="text-blue-600 hover:text-blue-800"
            >
              Already have an account? Sign in
            </button>
          </div>
        </div>
      ) : (
        <div>
          <LoginForm />
          <div className="text-center mt-4">
            <button
              onClick={() => setShowRegister(true)}
              className="text-blue-600 hover:text-blue-800"
            >
              Don't have an account? Register
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;