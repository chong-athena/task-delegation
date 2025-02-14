"use client";

import React, { useState, useEffect } from "react";
import {
  Table,
  Modal,
  Button,
  Checkbox,
  Form,
  Input,
  DatePicker,
  Typography
} from "antd";
import moment from "moment";

const { Title } = Typography;

export default function TaskManager() {
  const [tasks, setTasks] = useState([]);

  // For creating a new task
  const [showAddModal, setShowAddModal] = useState(false);
  // For editing an existing task
  const [showEditModal, setShowEditModal] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState(null);
  // For deleting a task
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState(null);
  // For showing instructions
  const [showInstructionsModal, setShowInstructionsModal] = useState(false);
  const [instructions, setInstructions] = useState(""); // We store fetched instructions here
  const [instructionsForTaskId, setInstructionsForTaskId] = useState(null);

  // Ant Design Form instances for Add / Edit
  const [addForm] = Form.useForm();
  const [editForm] = Form.useForm();

//   useEffect(() => {
//     fetchTasks();
//   }, []);

  // -------------------------
  // Fetch tasks
  // -------------------------
  const fetchTasks = () => {
    fetch("http://localhost:8000/api/tasks")
      .then((res) => res.json())
      .then((data) => setTasks(data))
      .catch((err) => console.error("Error fetching tasks:", err));
  };


  // Auto-refresh logic
  useEffect(() => {
    // Fetch tasks initially
    fetchTasks();

    // Set up auto-refresh every 10 seconds
    const intervalId = setInterval(() => {
      fetchTasks();
    }, 2000); // 10 seconds in milliseconds

    // Cleanup: Clear interval on component unmount
    return () => clearInterval(intervalId);
  }, []); // Empty dependency array means this runs once on mount


  // -------------------------
  // Toggle "done" (status) via checkbox
  // -------------------------
  const toggleDone = (task) => {
    const newStatus = task.status === "completed" ? "pending" : "completed";
    updateTaskStatus(task.id, newStatus);
  };

  const updateTaskStatus = (taskId, status) => {
    fetch(`http://localhost:8000/api/tasks/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    })
      .then((res) => res.json())
      .then(() => {
        setTasks((prev) =>
          prev.map((t) => (t.id === taskId ? { ...t, status } : t))
        );
      })
      .catch((err) => console.error("Error updating status:", err));
  };

  // -------------------------
  // Add a New Task
  // -------------------------
  const handleAddTask = (values) => {
    const { title, owner } = values;
    const due_time = values.due_time
      ? values.due_time.toISOString()
      : null;

    const newTask = {
      title,
      owner,
      due_time,
      status: "pending",
    };

    fetch("http://localhost:8000/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newTask),
    })
      .then((res) => res.json())
      .then((response) => {
        // Some backends return { task: {...} }, adjust if needed
        if (response.task) {
          setTasks((prev) => [...prev, response.task]);
        } else {
          // if your backend returns the whole task directly
          setTasks((prev) => [...prev, response]);
        }
        addForm.resetFields();
        setShowAddModal(false);
      })
      .catch((err) => console.error("Error adding task:", err));
  };

  // -------------------------
  // Edit an Existing Task
  // -------------------------
  const openEditModalFor = (task) => {
    setTaskToEdit(task);
    editForm.setFieldsValue({
      title: task.title,
      owner: task.owner,
      due_time: task.due_time ? moment(task.due_time) : null,
    });
    setShowEditModal(true);
  };

  const handleEditTask = (values) => {
    const { title, owner } = values;
    const due_time = values.due_time
      ? values.due_time.toISOString()
      : null;

    const updated = {
      ...taskToEdit,
      title,
      owner,
      due_time,
    };

    fetch(`http://localhost:8000/api/tasks/${taskToEdit.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    })
      .then((res) => res.json())
      .then((resUpdatedTask) => {
        // Update local state
        setTasks((prev) =>
          prev.map((t) => (t.id === resUpdatedTask.id ? resUpdatedTask : t))
        );
        setShowEditModal(false);
        setTaskToEdit(null);
      })
      .catch((err) => console.error("Error editing task:", err));
  };

  // -------------------------
  // Delete a Task
  // -------------------------
  const confirmDelete = (taskId) => {
    setTaskToDelete(taskId);
    setShowDeleteModal(true);
  };

  const handleDeleteTask = () => {
    fetch(`http://localhost:8000/api/tasks/${taskToDelete}`, {
      method: "DELETE",
    })
      .then(() => {
        setTasks((prev) => prev.filter((t) => t.id !== taskToDelete));
        setShowDeleteModal(false);
        setTaskToDelete(null);
      })
      .catch((err) => console.error("Error deleting task:", err));
  };

  // -------------------------
  // Show Instructions
  // (Now fetch from a separate endpoint /api/tasks/:taskId/instructions)
  // -------------------------
  const openInstructionsModalFor = (task) => {
    setInstructions("");
    setInstructionsForTaskId(task.id);
    setShowInstructionsModal(true);

    fetch(`http://localhost:8000/api/tasks/${task.id}/instructions`)
      .then((res) => res.json())
      .then((data) => {
        // data.instructions might have the actual text
        setInstructions(data.instructions || "No instructions found.");
      })
      .catch((err) => {
        console.error("Error fetching instructions:", err);
        setInstructions("Error fetching instructions.");
      });
  };

  // -------------------------
  // Table Columns
  // -------------------------
  const columns = [
    {
        title: "TASKS",
        key: "title",
        render: (_, record) => (
        <span
            style={{
            textDecoration:
                record.status === "completed" ? "line-through" : "none",
            }}
        >
            <Checkbox
            checked={record.status === "completed"}
            onChange={() => toggleDone(record)}
            style={{ marginRight: 8 }}
            />
            {record.title}
        </span>
        ),
    },
    {
        title: "OWNER",
        dataIndex: "owner",
        key: "owner",
        // For example: record.owner
    },
    {
    title: "SOURCE",
    dataIndex: "source",
    key: "source",
    render: (source) => source || "N/A", // Default to "N/A" if source is not set
  },
  {
    title: "DESCRIPTION",
    dataIndex: "description",
    key: "description",
    render: (desc) => desc || "No Description",
  },
    {
        title: "CREATED TIME",
        key: "created_at",
        render: (_, record) => {
        if (!record.created_at) return "N/A";
        // Convert from ISO to e.g. "YYYY-MM-DD HH:mm"
        return moment(record.created_at).format("YYYY-MM-DD HH:mm");
        },
    },
    {
        title: "DUE TIME",
        key: "due_date",
        render: (_, record) =>
        record.due_date
            ? moment(record.due_date).format("YYYY-MM-DD HH:mm")
            : "No due time",
    },
    {
      title: "ACTIONS",
      key: "actions",
      render: (_, record) => (
        <>
          <Button
            type="link"
            onClick={() => openEditModalFor(record)}
            style={{ marginRight: 8, color: "blue" }}
          >
            Edit
          </Button>
          <Button
            type="link"
            danger
            onClick={() => confirmDelete(record.id)}
            style={{ marginRight: 8 }}
          >
            Delete
          </Button>
          <Button
            type="link"
            onClick={() => openInstructionsModalFor(record)}
            style={{ color: "purple" }}
          >
            Show Instructions
          </Button>
        </>
      ),
    },
  ];

  return (
    <div style={{ padding: 20 }}>
      <Title level={2}>ToDo List</Title>
      <Button
        type="primary"
        onClick={() => setShowAddModal(true)}
        style={{ marginBottom: 20 }}
      >
        ADD NEW TASK +
      </Button>

      {/* ---------- TABLE ---------- */}
      <Table
        dataSource={tasks}
        columns={columns}
        rowKey={(record) => record.id}
      />

      {/* ---------- ADD TASK MODAL ---------- */}
      <Modal
        title="Add New Task"
        open={showAddModal}
        onCancel={() => setShowAddModal(false)}
        footer={null}
      >
        <Form form={addForm} layout="vertical" onFinish={handleAddTask}>
          <Form.Item
            label="Title"
            name="title"
            rules={[{ required: true, message: "Please enter a title." }]}
          >
            <Input />
          </Form.Item>

          <Form.Item label="Owner" name="owner">
            <Input />
          </Form.Item>

          {/* Removed instructions from the Add form */}

          <Form.Item label="Due Time" name="due_time">
            <DatePicker showTime />
          </Form.Item>

          <Form.Item>
            <Button htmlType="submit" type="primary">
              Add Task
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* ---------- EDIT TASK MODAL ---------- */}
      <Modal
        title="Edit Task"
        open={showEditModal}
        onCancel={() => {
          setShowEditModal(false);
          setTaskToEdit(null);
        }}
        footer={null}
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditTask}>
          <Form.Item
            label="Title"
            name="title"
            rules={[{ required: true, message: "Please enter a title." }]}
          >
            <Input />
          </Form.Item>

          <Form.Item label="Owner" name="owner">
            <Input />
          </Form.Item>

          {/* Removed instructions from the Edit form */}

          <Form.Item label="Due Time" name="due_time">
            <DatePicker showTime />
          </Form.Item>

          <Form.Item style={{ marginTop: 16 }}>
            <Button htmlType="submit" type="primary">
              Save Changes
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* ---------- DELETE CONFIRM MODAL ---------- */}
      <Modal
        title="Delete Task"
        open={showDeleteModal}
        onOk={handleDeleteTask}
        onCancel={() => setShowDeleteModal(false)}
        okText="Yes, Delete"
        cancelText="No"
        okButtonProps={{ danger: true }}
      >
        <p>Are you sure you want to delete this task?</p>
      </Modal>

      {/* ---------- SHOW INSTRUCTIONS MODAL ---------- */}
      <Modal
        title="Instructions / Suggested Solution"
        open={showInstructionsModal}
        onCancel={() => {
          setShowInstructionsModal(false);
          setInstructionsForTaskId(null);
        }}
        footer={[
          <Button
            key="close"
            onClick={() => {
              setShowInstructionsModal(false);
              setInstructionsForTaskId(null);
            }}
          >
            Close
          </Button>,
        ]}
      >
        {instructionsForTaskId ? (
          <div style={{ whiteSpace: "pre-wrap" }}>
            {instructions}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}