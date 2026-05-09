import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || 'Something went wrong.' };
  }

  componentDidCatch(error) {
    if (typeof this.props.onError === 'function') {
      this.props.onError(error);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <section className="panel error-fallback" role="alert">
          <h2>Something went wrong</h2>
          <p>{this.state.message}</p>
          <button type="button" className="btn compact" onClick={() => window.location.reload()}>
            Reload page
          </button>
        </section>
      );
    }

    return this.props.children;
  }
}