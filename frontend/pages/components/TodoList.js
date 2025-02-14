'use client';

import { useState, useEffect } from "react";

export default function TodoList() {
    const [tasks, setTasks] = useState([]);
    const [newTask, setNewTask] = useState("");

    useEffect(() => {
        fetch("http://localhost:8000/api/tasks")
            .then((response) => response.json())
            .then((data) => {
                if (Array.isArray(data)) {
                    setTasks(data);
                } else {
                    console.error("Invalid data format", data);
                }
            });
    }, []);

    const addTask = () => {
        fetch("http://localhost:8000/api/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task: newTask }),
        })
            .then((response) => response.json())
            .then(() => {
                setTasks([...tasks, { task: newTask, completed: false }]);
                setNewTask("");
            });
    };

    return (
        <div>
            <h1>Todo List</h1>
            <input
                type="text"
                value={newTask}
                onChange={(e) => setNewTask(e.target.value)}
                placeholder="New Task"
            />
            <button onClick={addTask}>Add Task</button>
            <ul>
                {Array.isArray(tasks) && tasks.map((task, index) => (
                    <li key={index}>{task.task}</li>
                ))}
            </ul>
        </div>
    );
}