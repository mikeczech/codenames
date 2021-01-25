import React, { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Switch,
  Redirect,
  Route,
  useParams
} from "react-router-dom";

export default function App() {
  return (
    <Router>
      <div>
        <Switch>
          <Route path="/:gameId">
            <Game />
          </Route>
          <Route path="/">
            <Create />
          </Route>
        </Switch>
      </div>
    </Router>
  );
}

class CreateGameForm extends React.Component {
  constructor(props) {
    super(props)
    this.state = {gameId: '', created: false}

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    this.setState({gameId: event.target.value});
  }

  handleSubmit(event) {
    (async () => {
      const rawResponse = await fetch('/api/create', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({gameId: this.state.gameId})
      });
      this.setState({created: true})
    })();
    event.preventDefault();
  }

  render() {
    if (this.state.created) {
      return <Redirect to={this.state.gameId} />
    }

    return (
      <form onSubmit={this.handleSubmit}>
        <label>
          Name:
          <input type="text" value={this.state.gameId} onChange={this.handleChange} />
        </label>
        <input type="submit" value="Submit" />
      </form>
    );
  }
}

function Create() {
  return <CreateGameForm />
}

class Square extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    return <button className={this.props.colorClass} >{this.props.word}</button>
  }
}


function Game() {
  const { gameId } = useParams();
  const [words, setWords] = useState(null);

  useEffect(() => {
      fetch(`/api/state?gameId=${gameId}`).then(res => res.json()).then(data => {
        setWords(data)
      });
  }, []);

  function renderSquare(w) {
    return <li><Square word={w["word"]} colorClass={w["color"]}/></li>
  }

  if (!words) {
    return <p>Loading state...</p>
  }

  return (
    <div>
      <ul className="words">{words.map(w => renderSquare(w))}</ul>
    </div>
  );
}
