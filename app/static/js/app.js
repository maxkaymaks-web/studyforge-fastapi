async function requestJson(url, options) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const detail = payload?.detail || "Request failed";
    throw new Error(detail);
  }
  return payload;
}

function setStatus(form, message, isError = false) {
  const statusNode = form.querySelector("[data-form-status]");
  if (!statusNode) {
    return;
  }
  statusNode.textContent = message;
  statusNode.style.color = isError ? "#b2491f" : "#165c49";
}

function bindLoginForm() {
  const form = document.querySelector("#login-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Выполняется вход...");
      await requestJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });
      window.location.href = "/dashboard";
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindRegisterForm() {
  const form = document.querySelector("#register-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Создаётся аккаунт...");
      await requestJson("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: formData.get("full_name"),
          email: formData.get("email"),
          password: formData.get("password"),
          role: formData.get("role"),
        }),
      });
      await requestJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });
      window.location.href = "/dashboard";
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindCourseForm() {
  const form = document.querySelector("#course-create-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Курс сохраняется...");
      await requestJson("/api/courses", {
        method: "POST",
        body: JSON.stringify({
          title: formData.get("title"),
          description: formData.get("description"),
          exam_date: formData.get("exam_date"),
          target_score: Number(formData.get("target_score")),
          weekly_hours_goal: Number(formData.get("weekly_hours_goal")),
          color_theme: formData.get("color_theme"),
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindCourseUpdateForm() {
  const form = document.querySelector("#course-update-form");
  if (!form) {
    return;
  }
  const courseId = Number(form.dataset.courseId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Изменения курса сохраняются...");
      await requestJson(`/api/courses/${courseId}`, {
        method: "PUT",
        body: JSON.stringify({
          title: formData.get("title"),
          description: formData.get("description"),
          exam_date: formData.get("exam_date"),
          target_score: Number(formData.get("target_score")),
          weekly_hours_goal: Number(formData.get("weekly_hours_goal")),
          color_theme: formData.get("color_theme"),
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindTopicForm() {
  const form = document.querySelector("#topic-create-form");
  if (!form) {
    return;
  }
  const courseId = Number(form.dataset.courseId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Тема сохраняется...");
      await requestJson("/api/topics", {
        method: "POST",
        body: JSON.stringify({
          course_id: courseId,
          title: formData.get("title"),
          description: formData.get("description"),
          difficulty: Number(formData.get("difficulty")),
          importance: Number(formData.get("importance")),
          estimated_minutes: Number(formData.get("estimated_minutes")),
          mastery_level: Number(formData.get("mastery_level")),
          status: formData.get("status"),
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindTopicUpdateForms() {
  const forms = document.querySelectorAll(".topic-update-form");
  for (const form of forms) {
    const topicId = Number(form.dataset.topicId);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        setStatus(form, "Тема обновляется...");
        await requestJson(`/api/topics/${topicId}`, {
          method: "PUT",
          body: JSON.stringify({
            title: formData.get("title"),
            description: formData.get("description"),
            difficulty: Number(formData.get("difficulty")),
            importance: Number(formData.get("importance")),
            estimated_minutes: Number(formData.get("estimated_minutes")),
            mastery_level: Number(formData.get("mastery_level")),
            status: formData.get("status"),
          }),
        });
        window.location.reload();
      } catch (error) {
        setStatus(form, error.message, true);
      }
    });
  }
}

function bindSessionForm() {
  const form = document.querySelector("#session-create-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Сессия сохраняется...");
      await requestJson("/api/sessions", {
        method: "POST",
        body: JSON.stringify({
          topic_id: Number(formData.get("topic_id")),
          planned_for: formData.get("planned_for"),
          actual_minutes: Number(formData.get("actual_minutes")),
          focus_score: Number(formData.get("focus_score")),
          notes: formData.get("notes"),
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindDeleteButtons() {
  const buttons = document.querySelectorAll("[data-delete-endpoint]");
  for (const button of buttons) {
    button.addEventListener("click", async () => {
      const endpoint = button.dataset.deleteEndpoint;
      const redirectUrl = button.dataset.redirectUrl || window.location.pathname;
      const confirmText = button.dataset.confirmText || "Удалить запись?";
      if (!window.confirm(confirmText)) {
        return;
      }
      try {
        await requestJson(endpoint, { method: "DELETE" });
        window.location.href = redirectUrl;
      } catch (error) {
        const ownerForm = button.closest("form");
        if (ownerForm) {
          setStatus(ownerForm, error.message, true);
          return;
        }
        window.alert(error.message);
      }
    });
  }
}

function bindQuizForm() {
  const form = document.querySelector("#quiz-create-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Результат сохраняется...");
      await requestJson("/api/quizzes", {
        method: "POST",
        body: JSON.stringify({
          topic_id: Number(formData.get("topic_id")),
          score: Number(formData.get("score")),
          max_score: Number(formData.get("max_score")),
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function readOptionalNumber(formData, key) {
  const rawValue = formData.get(key);
  if (rawValue === null || rawValue === "") {
    return null;
  }
  return Number(rawValue);
}

function bindFolderCreateForm() {
  const form = document.querySelector("#folder-create-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Папка создаётся...");
      await requestJson("/api/note-folders", {
        method: "POST",
        body: JSON.stringify({
          name: formData.get("name"),
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindNoteCreateButton() {
  const button = document.querySelector("#note-create-button");
  if (!button) {
    return;
  }
  button.addEventListener("click", async () => {
    try {
      const note = await requestJson("/api/notes", {
        method: "POST",
        body: JSON.stringify({
          title: "Новая заметка",
          body: "Опишите ключевые идеи, выводы и чек-лист здесь.",
          folder_id: button.dataset.folderId ? Number(button.dataset.folderId) : null,
          course_id: button.dataset.courseId ? Number(button.dataset.courseId) : null,
          topic_id: null,
          color_tone: "sunny",
          is_pinned: false,
        }),
      });
      const params = new URLSearchParams();
      params.set("note_id", String(note.id));
      if (button.dataset.folderId) {
        params.set("folder_id", button.dataset.folderId);
      }
      if (button.dataset.courseId) {
        params.set("course_id", button.dataset.courseId);
      }
      window.location.href = `/notes?${params.toString()}`;
    } catch (error) {
      window.alert(error.message);
    }
  });
}

function bindNoteUpdateForm() {
  const form = document.querySelector("#note-update-form");
  if (!form) {
    return;
  }
  const noteId = Number(form.dataset.noteId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      setStatus(form, "Заметка сохраняется...");
      await requestJson(`/api/notes/${noteId}`, {
        method: "PUT",
        body: JSON.stringify({
          title: formData.get("title"),
          body: formData.get("body"),
          folder_id: readOptionalNumber(formData, "folder_id"),
          course_id: readOptionalNumber(formData, "course_id"),
          topic_id: readOptionalNumber(formData, "topic_id"),
          color_tone: formData.get("color_tone"),
          is_pinned: formData.get("is_pinned") === "on",
        }),
      });
      window.location.reload();
    } catch (error) {
      setStatus(form, error.message, true);
    }
  });
}

function bindNoteTopicSync() {
  const form = document.querySelector("#note-update-form");
  if (!form) {
    return;
  }
  const courseSelect = form.querySelector('select[name="course_id"]');
  const topicSelect = form.querySelector('select[name="topic_id"]');
  if (!courseSelect || !topicSelect) {
    return;
  }

  courseSelect.addEventListener("change", async () => {
    const courseId = courseSelect.value;
    const previousTopicId = topicSelect.value;
    topicSelect.innerHTML = '<option value="">Без темы</option>';
    if (!courseId) {
      return;
    }
    try {
      const topics = await requestJson(`/api/topics?course_id=${courseId}`, { method: "GET" });
      for (const topic of topics) {
        const option = document.createElement("option");
        option.value = String(topic.id);
        option.textContent = topic.title;
        if (String(topic.id) === previousTopicId) {
          option.selected = true;
        }
        topicSelect.append(option);
      }
      if (!topics.some((topic) => String(topic.id) === previousTopicId)) {
        topicSelect.value = "";
      }
    } catch (error) {
      window.alert(error.message);
    }
  });
}

bindLoginForm();
bindRegisterForm();
bindCourseForm();
bindCourseUpdateForm();
bindTopicForm();
bindTopicUpdateForms();
bindSessionForm();
bindQuizForm();
bindFolderCreateForm();
bindNoteCreateButton();
bindNoteUpdateForm();
bindNoteTopicSync();
bindDeleteButtons();
