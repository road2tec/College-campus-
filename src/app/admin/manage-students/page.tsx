"use client";
import { useEffect, useState } from "react";
import { api, endpoints } from "@/lib/api";
import SectionTitle from "@/components/SectionTitle";
import { IconPlus, IconTrash, IconSearch, IconUpload } from "@tabler/icons-react";
import Image from "next/image";

export default function ManageStudentsPage() {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    rollNo: "",
    department: "",
    email: "",
    phone: "",
    file: null as File | null
  });

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const res = await api.get(endpoints.students.getAll);
      setStudents(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure?")) return;
    try {
      await api.delete(endpoints.students.delete(id));
      fetchStudents();
    } catch (err) {
      alert("Failed to delete");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.file) return alert("Please upload a photo");

    setLoading(true);
    const data = new FormData();
    data.append("name", formData.name);
    data.append("rollNo", formData.rollNo);
    data.append("department", formData.department);
    data.append("email", formData.email);
    data.append("phone", formData.phone);
    data.append("file", formData.file);

    try {
      await api.post(endpoints.students.add, data, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setIsModalOpen(false);
      setFormData({ name: "", rollNo: "", department: "", email: "", phone: "", file: null });
      fetchStudents();
      alert("Student Added Successfully!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to add student");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 h-full">
      <div className="flex justify-between items-center mb-6">
        <SectionTitle title="Manage Students" />
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary bg-teal-600 border-none hover:bg-teal-700 text-white gap-2"
        >
          <IconPlus size={20} /> Add Student
        </button>
      </div>

      <div className="card bg-base-100 shadow-sm border border-base-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="table table-lg">
            {/* head */}
            <thead className="bg-base-200/50 text-gray-600">
              <tr>
                <th>Profile</th>
                <th>Name / Roll No</th>
                <th>Department</th>
                <th>Contact</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-base-50 transition-colors">
                  <td>
                    <div className="avatar">
                      <div className="mask mask-squircle w-12 h-12 bg-gray-100">
                        {student.profileImage ? (
                          <img
                            src={`http://localhost:8001${student.profileImage}`}
                            alt={student.name}
                            onError={(e) => (e.currentTarget.src = 'https://ui-avatars.com/api/?name=' + student.name)}
                          />
                        ) : (
                          <div className="flex items-center justify-center h-full text-xs">{student.name[0]}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    <div className="font-bold text-gray-800">{student.name}</div>
                    <div className="text-sm opacity-50">{student.rollNo}</div>
                  </td>
                  <td>
                    <span className="badge badge-ghost badge-sm">{student.department}</span>
                  </td>
                  <td>
                    <div className="text-sm">{student.email}</div>
                    <div className="text-xs opacity-50">{student.phone}</div>
                  </td>
                  <td>
                    <button
                      onClick={() => handleDelete(student.id)}
                      className="btn btn-ghost btn-sm text-error"
                    >
                      <IconTrash size={18} />
                    </button>
                  </td>
                </tr>
              ))}
              {students.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-400">No students found. Add one to get started.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="card w-full max-w-lg bg-white shadow-2xl">
            <form onSubmit={handleSubmit} className="card-body">
              <h3 className="text-xl font-bold mb-4 text-gray-800">Add New Student</h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="form-control">
                  <label className="label text-xs font-semibold uppercase text-gray-500">Full Name</label>
                  <input required type="text" placeholder="John Doe" className="input input-bordered w-full"
                    value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                </div>
                <div className="form-control">
                  <label className="label text-xs font-semibold uppercase text-gray-500">Roll No</label>
                  <input required type="text" placeholder="CS-2024-01" className="input input-bordered w-full"
                    value={formData.rollNo} onChange={e => setFormData({ ...formData, rollNo: e.target.value })} />
                </div>
              </div>

              <div className="form-control">
                <label className="label text-xs font-semibold uppercase text-gray-500">Department</label>
                <select className="select select-bordered w-full"
                  value={formData.department} onChange={e => setFormData({ ...formData, department: e.target.value })} >
                  <option disabled value="">Select Department</option>
                  <option value="Computer Science">Computer Science</option>
                  <option value="Information Tech">Information Tech</option>
                  <option value="Electronics">Electronics</option>
                  <option value="Mechanical">Mechanical</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="form-control">
                  <label className="label text-xs font-semibold uppercase text-gray-500">Email</label>
                  <input required type="email" placeholder="john@example.com" className="input input-bordered w-full"
                    value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                </div>
                <div className="form-control">
                  <label className="label text-xs font-semibold uppercase text-gray-500">Phone</label>
                  <input required type="text" placeholder="9876543210" className="input input-bordered w-full"
                    value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} />
                </div>
              </div>

              <div className="form-control">
                <label className="label text-xs font-semibold uppercase text-gray-500">Photo (For Face ID)</label>
                <input required type="file" className="file-input file-input-bordered w-full" accept="image/*"
                  onChange={e => setFormData({ ...formData, file: e.target.files ? e.target.files[0] : null })} />
                <label className="label">
                  <span className="label-text-alt text-warning">Must be a clear front-facing photo</span>
                </label>
              </div>

              <div className="card-actions justify-end mt-6">
                <button type="button" className="btn btn-ghost" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" disabled={loading} className="btn btn-primary bg-teal-600 text-white">
                  {loading ? <span className="loading loading-spinner"></span> : "Save Student"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
