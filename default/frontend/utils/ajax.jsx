const toFormData = data => {
  const formData = new FormData();
  for (var key in data) {
    formData.append(key, data[key]);
  }
  return formData;
};

const toURIParams = data => {
  const params = new URLSearchParams();
  for (let key in data) {
    params.append(key, data[key]);
  }
  return params.toString();
};

const ajax = (method, url, data) => {
  method = method.toUpperCase();
  return new Promise((resolve, reject) => {
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
      if ((this.status >= 200 && this.status < 300) || this.status == 403) {
        resolve(xhr.response);
      } else {
        reject({
          status: this.status,
          statusText: xhr.statusText
        });
      }
    };
    xhr.onerror = function() {
      reject({
        status: this.status,
        statusText: xhr.statusText
      });
    };
    if (method == 'GET') {
      xhr.open(method, `${url}?${toURIParams(data)}`);
      xhr.send();
    } else {
      xhr.open(method, url);
      xhr.send(toFormData(data));
    }
  });
};

const ajaxAndReturnJson = async (method, url, data) => {
  const res = await ajax(method, url, data);
  return JSON.parse(res);
};

export { ajax, ajaxAndReturnJson };
