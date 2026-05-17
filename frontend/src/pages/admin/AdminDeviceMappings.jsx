import React, { useState, useEffect, useRef } from 'react';
import AdminLayout from '../../components/layouts/AdminLayout';

const AdminDeviceMappings = () => {
  const [mappings, setMappings] = useState([]);
  const [members, setMembers] = useState([]);
  const [trainers, setTrainers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    device_user_id: '',
    person_type: 'member',
    person_id: ''
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchMappings();
    fetchMembers();
    fetchTrainers();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchMappings = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/attendance/mappings', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMappings(data.mappings);
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/admin/members?limit=1000', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
      }
    } catch (err) {
      console.error('Failed to fetch members:', err);
    }
  };

  const fetchTrainers = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/admin/trainers?limit=1000', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTrainers(data.trainers || []);
      }
    } catch (err) {
      console.error('Failed to fetch trainers:', err);
    }
  };

  // Filter members/trainers based on search query
  const getFilteredOptions = () => {
    const options = formData.person_type === 'member' ? members : trainers;
    if (!searchQuery.trim()) return options;
    
    const query = searchQuery.toLowerCase();
    return options.filter(option => {
      const name = option.full_name?.toLowerCase() || '';
      const id = option.member_number?.toString().toLowerCase() || option.id?.substring(0, 8).toLowerCase() || '';
      return name.includes(query) || id.includes(query);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/attendance/mappings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        setFormData({ device_user_id: '', person_type: 'member', person_id: '' });
        setSearchQuery('');
        setShowForm(false);
        setShowDropdown(false);
        fetchMappings();
      } else {
        const data = await res.json();
        setError(data.error);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSelectPerson = (personId) => {
    setFormData({ ...formData, person_id: personId });
    setSearchQuery('');
    setShowDropdown(false);
  };

  const handlePersonTypeChange = (newType) => {
    setFormData({ ...formData, person_type: newType, person_id: '' });
    setSearchQuery('');
    setShowDropdown(false);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this mapping?')) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/attendance/mappings/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchMappings();
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <AdminLayout><div className="p-8 text-white">Loading...</div></AdminLayout>;

  return (
    <AdminLayout>
    <div className="p-8 bg-fitnix-black min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-fitnix-off-white">Device User <span className="fitnix-gradient-text">Mappings</span></h1>
            <p className="text-fitnix-off-white/60 mt-1">Link biometric device users to members and trainers</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-fitnix-lime text-fitnix-black px-6 py-2 rounded-lg hover:bg-fitnix-lime/90 font-semibold transition-colors"
          >
            {showForm ? 'Cancel' : 'Add Mapping'}
          </button>
        </div>

        {error && <div className="mb-4 p-4 bg-red-500/10 border border-red-500 text-red-400 rounded-lg">{error}</div>}

        {showForm && (
          <div className="bg-fitnix-charcoal border border-fitnix-dark-gray p-6 rounded-lg shadow mb-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2 text-fitnix-off-white">Device User ID</label>
                <input
                  type="text"
                  value={formData.device_user_id}
                  onChange={(e) => setFormData({ ...formData, device_user_id: e.target.value })}
                  className="w-full px-4 py-2 bg-fitnix-dark-gray border border-fitnix-gray/30 rounded-lg text-fitnix-off-white focus:border-fitnix-lime focus:outline-none"
                  placeholder="Enter device user ID (e.g., 1, 7, 9)"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2 text-fitnix-off-white">Person Type</label>
                <select
                  value={formData.person_type}
                  onChange={(e) => handlePersonTypeChange(e.target.value)}
                  className="w-full px-4 py-2 bg-fitnix-dark-gray border border-fitnix-gray/30 rounded-lg text-fitnix-off-white focus:border-fitnix-lime focus:outline-none"
                >
                  <option value="member">Member</option>
                  <option value="trainer">Trainer</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2 text-fitnix-off-white">
                  {formData.person_type === 'member' ? 'Search Member' : 'Search Trainer'}
                </label>
                <div ref={dropdownRef} className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setShowDropdown(true);
                    }}
                    onFocus={() => setShowDropdown(true)}
                    placeholder={`Search by name or ID...`}
                    className="w-full px-4 py-2 bg-fitnix-dark-gray border border-fitnix-gray/30 rounded-lg text-fitnix-off-white focus:border-fitnix-lime focus:outline-none"
                  />
                  
                  {showDropdown && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-fitnix-dark-gray border border-fitnix-gray/30 rounded-lg shadow-lg max-h-64 overflow-y-auto z-10">
                      {getFilteredOptions().length === 0 ? (
                        <div className="px-4 py-3 text-fitnix-gray text-sm">
                          No {formData.person_type}s found
                        </div>
                      ) : (
                        getFilteredOptions().map(option => (
                          <button
                            key={option.id}
                            type="button"
                            onClick={() => handleSelectPerson(option.id)}
                            className="w-full text-left px-4 py-2 hover:bg-fitnix-gray/20 text-fitnix-off-white transition-colors border-b border-fitnix-dark-gray/50 last:border-b-0"
                          >
                            <div className="font-medium">{option.full_name}</div>
                            <div className="text-xs text-fitnix-gray">
                              ID: {option.member_number || option.id.substring(0, 8)}
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
                {formData.person_id && (
                  <div className="mt-2 p-2 bg-fitnix-lime/10 border border-fitnix-lime/30 rounded text-sm text-fitnix-lime">
                    ✓ Selected: {
                      (formData.person_type === 'member' ? members : trainers).find(p => p.id === formData.person_id)?.full_name
                    }
                  </div>
                )}
              </div>
              <button
                type="submit"
                disabled={!formData.device_user_id || !formData.person_id}
                className="bg-fitnix-lime text-fitnix-black px-6 py-2 rounded-lg hover:bg-fitnix-lime/90 font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Mapping
              </button>
            </form>
          </div>
        )}

        <div className="bg-fitnix-charcoal border border-fitnix-dark-gray rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-fitnix-dark-gray/50 border-b border-fitnix-dark-gray">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-fitnix-lime">Device User ID</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-fitnix-lime">Person Type</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-fitnix-lime">Member/Trainer ID</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-fitnix-lime">Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-fitnix-lime">Actions</th>
              </tr>
            </thead>
            <tbody>
              {mappings.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-fitnix-gray">
                    No mappings yet. Click "Add Mapping" to create one.
                  </td>
                </tr>
              ) : (
                mappings.map(mapping => {
                  // Get the person's member_number or ID
                  const person = (mapping.person_type === 'member' ? members : trainers).find(p => p.id === mapping.person_id);
                  const displayId = person?.member_number || mapping.person_id.substring(0, 8);
                  const displayName = mapping.person_name || person?.full_name || 'Unknown';
                  
                  return (
                    <tr key={mapping.id} className="border-b border-fitnix-dark-gray hover:bg-fitnix-dark-gray/30 transition-colors">
                      <td className="px-6 py-3 text-fitnix-off-white font-medium">{mapping.device_user_id}</td>
                      <td className="px-6 py-3 text-fitnix-gray capitalize">{mapping.person_type}</td>
                      <td className="px-6 py-3 text-fitnix-lime font-semibold">{displayId}</td>
                      <td className="px-6 py-3 text-fitnix-off-white">{displayName}</td>
                      <td className="px-6 py-3">
                        <button
                          onClick={() => handleDelete(mapping.id)}
                          className="text-red-400 hover:text-red-300 text-sm font-semibold transition-colors"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
    </AdminLayout>
  );
};

export default AdminDeviceMappings;
