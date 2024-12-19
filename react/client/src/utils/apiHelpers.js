const API_BASE_URL = 'http://127.0.0.1:5001/api';

export const fetchTransformations = async () => {
  const response = await fetch(`${API_BASE_URL}/transformations`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch transformations');
  }
  return data;
};

export const uploadFile = async (fileContent) => {
  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ file: fileContent }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to upload file');
  }
  return data;
};

export const fetchPreview = async () => {
  const response = await fetch(`${API_BASE_URL}/preview`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch preview');
  }
  return data;
};

export const previewColumn = async (column) => {
  const response = await fetch(`${API_BASE_URL}/preview_column`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ column }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to preview column');
  }
  return data;
};

export const previewTransform = async (column, transformation) => {
  const response = await fetch(`${API_BASE_URL}/preview_transform`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ column, transformation }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to preview transformation');
  }
  return data;
};

export const applyTransform = async (column, transformation) => {
  const response = await fetch(`${API_BASE_URL}/transform`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ column, transformation }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to apply transformation');
  }
  return data;
};

export const saveToCSV = async (selectedColumns) => {
  const response = await fetch(`${API_BASE_URL}/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ columns: selectedColumns }),
  });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'transformed_data.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};
