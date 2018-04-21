import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';

import Routes from 'routes';
import Store from 'store';

const App = props => (
  <Provider store={props.store}>
    <Routes />
  </Provider>
);

const store = Store();

ReactDOM.render(<App store={store} />, document.getElementById('root'));
