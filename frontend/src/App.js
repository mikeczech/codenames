import React, { useEffect, useState } from "react";
import { v4 as uuidv4 } from 'uuid';
import Cookies from 'universal-cookie';
import {
  BrowserRouter as Router,
  Switch,
  Redirect,
  Route,
  useParams
} from "react-router-dom";

const RED_COLOR_ID = 1;
const BLUE_COLOR_ID = 2;
const PLAYER_ROLE_ID = 1;
const SPYMASTER_ROLE_ID = 2;

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
    this.state = {gameName: '', created: false, gameId: null}

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    this.setState({gameName: event.target.value});
  }

  handleSubmit(event) {
    (async () => {
      fetch('/games/', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({name: this.state.gameName})
      })
      .then(response => response.json())
      .then(json => {
        this.setState({created: true, gameId: json['game_id']})
      })
      .catch(e => {
        console.log(e)
      });
    })();
    event.preventDefault();
  }

  render() {
    if (this.state.created) {
      return <Redirect to={this.state.gameId.toString()} />
    }

    return (
      <form onSubmit={this.handleSubmit}>
        <label>
          <h1 className="text-3xl font-medium" >Name:</h1>
          <input type="text" value={this.state.gameName} onChange={this.handleChange} />
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


function colorIdToClass(colorId) {
  if(colorId === 1) {
    return "red";
  } else if (colorId === 2) {
    return "blue";
  } else if (colorId === 3) {
    return "neutral";
  } else if (colorId === 4) {
    return "assassin";
  }
  throw new Error("Unknown color id")
}


function Game() {
  const { gameId } = useParams();
  const [words, setWords] = useState(null);
  const [playerName, setPlayerName] = useState(null);

  useEffect(() => {
      fetch(`/games/${gameId}/words`).then(res => res.json()).then(data => {
        setWords(data)
      });
      const cookies = new Cookies();
      if(typeof cookies.get("session_id") === 'undefined') {
        cookies.set("session_id", uuidv4(), { path: '/'});
      };
  }, []);

  function renderSquare(w) {
    return <li><Square word={w["word"]} colorClass={colorIdToClass(w["color"])}/></li>
  }

  function handleJoin(colorId, roleId) {
    (async () => {
      fetch(`/games/${gameId}/join`, {
        method: 'PUT',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({color_id: colorId, role_id: roleId, name: playerName})
      })
      .then(response => response.json())
      .then(json => {
        this.setState({})
      })
      .catch(e => {
        console.log(e)
      });
    })();
  }

  function handlePlayerNameChange(event) {
    setPlayerName(event.target.value);
  }

  if (!words) {
    return <p>Loading state...</p>
  }

  return (
    <div>
      <div>
        <form>
          <label>
            Username:
            <input type="text" onChange={e => handlePlayerNameChange(e)} />
          </label>
        </form>
      </div>
      <ul className="words">{words.map(w => renderSquare(w))}</ul>
      <form>
        <div>
          <button onClick={() => handleJoin(RED_COLOR_ID, SPYMASTER_ROLE_ID)}>Join as spymaster (red)</button>
        </div>
        <div>
          <button onClick={() => handleJoin(RED_COLOR_ID, PLAYER_ROLE_ID)}>Join as agent (red)</button>
        </div>
        <div>
          <button onClick={() => handleJoin(BLUE_COLOR_ID, SPYMASTER_ROLE_ID)}>Join as spymaster (blue)</button>
        </div>
        <div>
          <button onClick={() => handleJoin(BLUE_COLOR_ID, PLAYER_ROLE_ID)}>Join as agend (blue)</button>
        </div>
      </form>
    </div>
  );
}
