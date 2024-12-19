export const prepareChartData = (data, column, type) => {
  console.log('prepareChartData input:', { data, column, type }); // Debug log

  if (!data || !column) return [];

  // For histogram data (numerical)
  if (type === 'numeric') {
    try {
      console.log('Processing numeric data:', data); // Debug log

      // If data is already in {category, count} format
      if (Array.isArray(data) && data[0] && 'category' in data[0] && 'count' in data[0]) {
        console.log('Data is already in correct format'); // Debug log
        return data;
      }

      // Handle case where data might be nested in an array
      if (Array.isArray(data) && data[0] && data[0].bins && Array.isArray(data[0].counts)) {
        console.log('Found bins and counts in first array element'); // Debug log
        return data[0].bins.map((bin, index) => ({
          category: bin,
          count: parseInt(data[0].counts[index])
        }));
      }

      // Handle case where data has direct bins and counts properties
      if (data.bins && Array.isArray(data.counts)) {
        console.log('Found direct bins and counts'); // Debug log
        return data.bins.map((bin, index) => ({
          category: bin,
          count: parseInt(data.counts[index])
        }));
      }

      // Handle case where data is in an object
      if (typeof data === 'object' && !Array.isArray(data)) {
        const firstValue = Object.values(data)[0];
        if (firstValue && typeof firstValue === 'object') {
          if (firstValue.bins && Array.isArray(firstValue.counts)) {
            console.log('Found bins and counts in first object value'); // Debug log
            return firstValue.bins.map((bin, index) => ({
              category: bin,
              count: parseInt(firstValue.counts[index])
            }));
          }
        }
      }

      // Handle case where data is a simple array of values
      if (Array.isArray(data)) {
        // Create bins for the data
        const values = data.filter(val => val !== null && !isNaN(val));
        if (values.length === 0) return [];

        const min = Math.min(...values);
        const max = Math.max(...values);
        const binCount = 10;
        const binSize = (max - min) / binCount;

        const bins = new Array(binCount).fill(0);
        values.forEach(value => {
          const binIndex = Math.min(Math.floor((value - min) / binSize), binCount - 1);
          bins[binIndex]++;
        });

        return bins.map((count, index) => ({
          category: `${(min + index * binSize).toFixed(2)} - ${(min + (index + 1) * binSize).toFixed(2)}`,
          count: count
        }));
      }

      console.error('Unexpected numeric data format:', data);
      return [];
    } catch (error) {
      console.error('Error preparing histogram data:', error);
      console.error('Data received:', data);
      return [];
    }
  }

  // For categorical data
  try {
    console.log('Processing categorical data:', data); // Debug log

    // If data is already in the correct format
    if (Array.isArray(data) && data[0] && 'category' in data[0] && 'count' in data[0]) {
      console.log('Categorical data already in correct format'); // Debug log
      return data;
    }

    const valueMap = new Map();
    const dataToProcess = Array.isArray(data) ? data : Object.values(data);
    
    dataToProcess.forEach(item => {
      const value = typeof item === 'object' ? item[column] : item;
      const strValue = String(value);
      valueMap.set(strValue, (valueMap.get(strValue) || 0) + 1);
    });

    const result = Array.from(valueMap.entries())
      .map(([category, count]) => ({
        category,
        count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 15);

    console.log('Processed categorical result:', result); // Debug log
    return result;
  } catch (error) {
    console.error('Error preparing categorical data:', error);
    console.error('Data received:', data);
    return [];
  }
};

export const getTransformedColumnNames = (column, transformation) => {
  return (columns) => {
    switch (transformation) {
      case 'standardization':
        return [`${column}_standardized`];
      case 'minmax':
        return [`${column}_minmax`];
      case 'log':
        return [`${column}_log`];
      case 'label':
        return [`${column}_label`];
      case 'onehot':
        return columns.filter(col => col.startsWith(`${column}_`));
      case 'remove_nulls':
        return [];
      default:
        return [];
    }
  };
};
