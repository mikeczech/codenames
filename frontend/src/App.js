import React, { useEffect, useState, useRef } from "react";
import { v4 as uuidv4 } from 'uuid';
import Cookies from 'universal-cookie';
import {
  BrowserRouter as Router,
  Routes,
  Navigate,
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
        <Routes>
          <Route path="/:gameId" element={<Game />} />
          <Route path="/" element={<Create />} />
        </Routes>
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
      return <Navigate to={this.state.gameId.toString()} />
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
  render() {
    return <button className={this.props.colorClass} >{this.props.word}</button>
  }
}

class Login extends React.Component {
  state = {
    playerName: "",
    gameId: 0
  }

  getPlayer = (colorId, roleId) => {
    return this.props.gameState.players.find(p => p.color._value_ === colorId && p.role._value_ === roleId)
  }

  handleJoin = (colorId, roleId) => {
    (async () => {
      fetch(`/games/${this.props.gameId}/join`, {
        method: 'PUT',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({color_id: colorId, role_id: roleId, name: this.state.playerName})
      })
      .then(response => response.json())
      .then(json => {})
      .catch(e => {
        console.log(e)
      });
    })();
  }

  handlePlayerNameChange = (event) => {
    this.state.playerName = event.target.value;
  }

  startGame = () => {
    (async () => {
      fetch(`/games/${this.props.gameId}/start`, {
        method: 'PUT',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
      .then(response => response.json())
      .then(json => {})
      .catch(e => {
        console.log(e)
      });
    })();
  }

  render() {
    var redSpyMasterHasJoined = this.getPlayer(RED_COLOR_ID, SPYMASTER_ROLE_ID) !== undefined
    var blueSpyMasterHasJoined = this.getPlayer(BLUE_COLOR_ID, SPYMASTER_ROLE_ID) !== undefined
    var redPlayerHasJoined = this.getPlayer(RED_COLOR_ID, PLAYER_ROLE_ID) !== undefined
    var bluePlayerHasJoined = this.getPlayer(BLUE_COLOR_ID, PLAYER_ROLE_ID) !== undefined
    var allJoined = redSpyMasterHasJoined && blueSpyMasterHasJoined && redPlayerHasJoined && bluePlayerHasJoined

    return <div className="modal fixed w-full h-full top-0 left-0 flex items-center justify-center">
        <div className="modal-overlay absolute w-full h-full bg-gray-900 opacity-80"></div>
        <div className="modal-container bg-white w-11/12 md:max-w-md mx-auto rounded shadow-lg z-50 overflow-y-auto">

          <div className="modal-content py-4 text-left px-6">
            <div className="flex justify-between items-center pb-3">
              <p className="text2xl font-bold">Join the Game</p>
            </div>

            <form>
              <input className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
                     type="text"
                     placeholder="Your Name"
                     //disabled=false
                     onChange={e => this.handlePlayerNameChange(e)}
              />
            </form>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => this.handleJoin(RED_COLOR_ID, SPYMASTER_ROLE_ID)}
                disabled={redSpyMasterHasJoined}
                className={
                  this.getPlayer(RED_COLOR_ID, SPYMASTER_ROLE_ID) ?
                  "modal-close px-4 bg-gray-400 p-3 rounded-lg text-white" :
                  "modal-close px-4 bg-red-500 p-3 rounded-lg text-white hover:bg-gray-400"
                }>
                {this.getPlayer(RED_COLOR_ID, SPYMASTER_ROLE_ID) ? this.getPlayer(RED_COLOR_ID, SPYMASTER_ROLE_ID).name : "Join as Spymaster" }
              </button>
              <button
                onClick={() => this.handleJoin(BLUE_COLOR_ID, SPYMASTER_ROLE_ID)}
                disabled={blueSpyMasterHasJoined}
                className={
                  this.getPlayer(BLUE_COLOR_ID, SPYMASTER_ROLE_ID) ?
                  "modal-close px-4 bg-gray-400 p-3 rounded-lg text-white" :
                  "modal-close px-4 bg-blue-500 p-3 rounded-lg text-white hover:bg-gray-400"
                }>
                {this.getPlayer(BLUE_COLOR_ID, SPYMASTER_ROLE_ID) ? this.getPlayer(BLUE_COLOR_ID, SPYMASTER_ROLE_ID).name : "Join as Spymaster" }
              </button>
              <button
                onClick={() => this.handleJoin(RED_COLOR_ID, PLAYER_ROLE_ID)}
                disabled={redPlayerHasJoined}
                className={
                  this.getPlayer(RED_COLOR_ID, PLAYER_ROLE_ID) ?
                  "modal-close px-4 bg-gray-400 p-3 rounded-lg text-white" :
                  "modal-close px-4 bg-red-500 p-3 rounded-lg text-white hover:bg-gray-400"
                }>
                {this.getPlayer(RED_COLOR_ID, PLAYER_ROLE_ID) ? this.getPlayer(RED_COLOR_ID, PLAYER_ROLE_ID).name : "Join as Player" }
              </button>
              <button
                onClick={() => this.handleJoin(BLUE_COLOR_ID, PLAYER_ROLE_ID)}
                disabled={bluePlayerHasJoined}
                className={
                  this.getPlayer(BLUE_COLOR_ID, PLAYER_ROLE_ID) ?
                  "modal-close px-4 bg-gray-400 p-3 rounded-lg text-white" :
                  "modal-close px-4 bg-blue-500 p-3 rounded-lg text-white hover:bg-gray-400"
                }>
                {this.getPlayer(BLUE_COLOR_ID, PLAYER_ROLE_ID) ? this.getPlayer(BLUE_COLOR_ID, PLAYER_ROLE_ID).name : "Join as Player" }
              </button>
            </div>
            <div className="grid grid-cols-1 mt-4 gap-4">
              <button
                onClick={this.startGame}
                disabled={!(allJoined)}
                className={
                  allJoined ?
                  "modal-close px-4 bg-black p-3 rounded-lg text-white hover:bg-gray-400" :
                  "modal-close px-4 bg-gray-400 p-3 rounded-lg text-white"
                }>
                Start Game
              </button>
            </div>
          </div>

        </div>
      </div>
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
  const [gameState, setGameState] = useState(null);
  const modalDiv = useRef(null)

  useEffect(() => {
      fetch(`/games/${gameId}/words`).then(res => res.json()).then(data => {
        setWords(data)
      });
      const cookies = new Cookies();
      if(typeof cookies.get("session_id") === 'undefined') {
        cookies.set("session_id", uuidv4(), { path: '/'});
      };

      const evtSource = new EventSource(`http://127.0.0.1:8000/updates/${gameId}`);
      evtSource.addEventListener("new_message", function (event) {
        const parsedData = JSON.parse(event.data);
        setGameState(parsedData);
      });

      return () => {
        evtSource.close();
      };
  }, []);

  function renderSquare(w) {
    return <li key={w["word"]}><Square word={w["word"]} colorClass={colorIdToClass(w["color"])}/></li>
  }

  if (!words) {
    return <p>Loading state...</p>
  }

  return (
    <div>
      <Login gameState={gameState} gameId={gameId} />
      <ul className="words">{words.map(w => renderSquare(w))}</ul>
    </div>
  );
}
