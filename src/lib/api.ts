import axios from "axios";

const API_URL = "http://localhost:8001";

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

export const endpoints = {
    auth: {
        login: "/admin/login",
    },
    students: {
        getAll: "/students/",
        add: "/students/add",
        delete: (id: string) => `/students/${id}`,
    },
    attendance: {
        mark: "/attendance/mark",
        today: "/attendance/today",
        stats: "/attendance/stats",
    },
};
