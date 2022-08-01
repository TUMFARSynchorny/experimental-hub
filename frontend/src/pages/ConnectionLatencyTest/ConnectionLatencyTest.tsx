import * as React from "react";
import { useRef, useEffect, useState } from "react";

import "./ConnectionLatencyTest.css";
import Connection from "../../networking/Connection";
import ConnectionState from "../../networking/ConnectionState";
import jsQR from "jsqr";
import Chart from "chart.js/auto";
import { avg, median } from "./util";
import { EvaluationResults, LocalStreamData, MergedData, RemoteStreamData } from "./def";

var QRCode = require("qrcode");

/**
 * Test page for testing the {@link Connection} & api.
 */
const ConnectionLatencyTest = (props: {
  localStream?: MediaStream,
  setLocalStream: (localStream: MediaStream) => void,
  connection: Connection,
  setConnection: (connection: Connection) => void,
}) => {
  const connection = props.connection;
  const defaultConfig = {
    participantId: connection.participantId ?? "",
    sessionId: connection.sessionId ?? "",
    fps: 30,
    background: true,
    width: 640,
    height: 480,
    qrCodeSize: 200,
    printTime: true,
    outlineQrCode: false,
  };
  const [connectionState, setConnectionState] = useState(connection.state);
  const [startedRemoteStreamLoop, setStartedRemoteStreamLoop] = useState(false);
  const [remoteStreamData, setRemoteStreamData] = useState<RemoteStreamData[]>([]);
  const [localStreamData, setLocalStreamData] = useState<LocalStreamData[]>([]);
  const [mergedData, setMergedData] = useState<MergedData[] | undefined>();
  const [config, setConfig] = useState<TestConfigObj>(defaultConfig);
  const canvasQRRef = useRef<HTMLCanvasElement>(null);
  const canvasLocalRef = useRef<HTMLCanvasElement>(null);
  const canvasRemoteRef = useRef<HTMLCanvasElement>(null);
  const latencyRef = useRef<HTMLSpanElement>(null);
  const stopped = useRef(false);

  // Register Connection event handlers 
  useEffect(() => {
    /** Handle `connectionStateChange` event of {@link Connection}. */
    const stateChangeHandler = async (state: ConnectionState) => {
      console.log(`%cConnection state change Handler: ${ConnectionState[state]}`, "color:blue");
      setConnectionState(state);
      if (state === ConnectionState.CLOSED || state === ConnectionState.FAILED) {
        stopped.current = true;
        console.group("Remote Stream Data");
        console.log(remoteStreamData);
        console.groupEnd();
        console.group("Local Stream Data");
        console.log(localStreamData);
        console.log("avg", avg(localStreamData.map(d => d.qrCodeGenerationTime)));
        console.log("median", median(localStreamData.map(d => d.qrCodeGenerationTime)));
        console.groupEnd();
      }
    };

    /** Handle `remoteStreamChange` event of {@link Connection}. */
    const streamChangeHandler = async (_: MediaStream) => {
      console.log("%cRemote Stream Change Handler", "color:blue");
      // Start update loop for remote canvas when remote stream is received;
      if (!startedRemoteStreamLoop) {
        setStartedRemoteStreamLoop(true);
        updateRemoteCanvas();
      }
    };

    connection.on("remoteStreamChange", streamChangeHandler);
    connection.on("connectionStateChange", stateChangeHandler);
    return () => {
      // Remove event handlers when component is deconstructed
      connection.off("remoteStreamChange", streamChangeHandler);
      connection.off("connectionStateChange", stateChangeHandler);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connection, config, startedRemoteStreamLoop, remoteStreamData]);

  /** Start the connection experiment */
  const start = async () => {
    console.log("Start Test. Config:", config);

    // Setup local canvas stream
    const localCanvasStream = canvasLocalRef.current.captureStream();
    props.setLocalStream(localCanvasStream); // Note: setLocalStream is not executed / updated right away. See useState react docs 

    // Start update loop for local stream canvas
    try {
      await updateLocalCanvas();
    } catch (error) {
      console.warn("Aborting start");
      return;
    }

    // Start connection
    connection.start(localCanvasStream);
  };

  /** Stop the connection experiment */
  const stop = async () => {
    connection.stop();
    combineData();
  };

  /** 
   * Combines data from `localStreamData` and `remoteStreamData`.
   * Currently takes the `qrCodeGenerationTime` from `localStreamData` and matches and copies it into `remoteStreamData`.
   */
  const combineData = () => {
    // Create lookup table based on localStreamData array (convert to object)
    const lookup: { [key: number]: number; } = {};
    localStreamData.forEach(e => {
      lookup[e.timestamp] = e.qrCodeGenerationTime;
    });

    const newMergedData: MergedData[] = remoteStreamData.map(e => {
      const qrCodeGenerationTime = lookup[e.qrCodeTimestamp];
      return {
        ...e,
        qrCodeGenerationTime: qrCodeGenerationTime,
        trueLatency: e.latency - qrCodeGenerationTime
      };
    });
    console.group("Merged Data");
    console.log(newMergedData);
    console.groupEnd();
    setMergedData(newMergedData);
  };

  /** Measure latency between the remote stream QR-code and current time. */
  const getLatency = () => {
    const localTimestamp = window.performance.now();
    const qrCodeTimestamp = parseQRCode(canvasRemoteRef.current);
    const diff = localTimestamp - qrCodeTimestamp;
    if (latencyRef.current) {
      latencyRef.current.innerText = `${diff.toFixed(4)}`;
    }
    return [diff, localTimestamp, qrCodeTimestamp];
  };

  /** Log a data point in `data`. */
  const makeLogEntry = async () => {
    let latency: number, timestamp: number, qrCodeTimestamp: number;
    const startTime = window.performance.now();
    try {
      [latency, timestamp, qrCodeTimestamp] = getLatency();
    } catch (error) {
      latency = null;
      qrCodeTimestamp = null;
      timestamp = window.performance.now();
    }
    const latencyMethodRuntime = window.performance.now() - startTime;

    const remoteStreamSettings = connection.remoteStream.getVideoTracks()[0].getSettings();
    const entry: RemoteStreamData = {
      latency: latency,
      fps: remoteStreamSettings.frameRate,
      timestamp: timestamp,
      qrCodeTimestamp: qrCodeTimestamp,
      frame: remoteStreamData.length,
      latencyMethodRuntime: latencyMethodRuntime,
      dimensions: {
        width: remoteStreamSettings.width,
        height: remoteStreamSettings.height
      }
      // connectionStats: await connection.getStats()
    };
    // console.log(entry);
    remoteStreamData.push(entry);
  };

  /** Parse the QR code in `canvas`. */
  const parseQRCode = (canvas: HTMLCanvasElement) => {
    // Calculate position of QR code, in case transmitted image is scaled down.
    const qrCodeWidth = Math.floor((canvas.width / config.width) * config.qrCodeSize);
    const qrCodeHeight = Math.floor((canvas.height / config.height) * config.qrCodeSize);
    const context = canvas.getContext("2d");

    // Get image data for expected position of QR code. Getting only part of the image saves a lot of time in `jsQR` (optimization).
    const imageData = context.getImageData(0, 0, qrCodeWidth, qrCodeHeight);

    // Draw a rectangle around the expected position of the QR code (debugging)
    if (config.outlineQrCode) {
      // console.log("canvas width:", canvas.width, "canvas height:", canvas.height, "config width:", config.width, "config height:", config.height, "config qrCodeSize:", config.qrCodeSize);
      // console.log(qrCodeWidth, qrCodeHeight);
      context.beginPath();
      context.lineWidth = 2;
      context.strokeStyle = "red";
      context.rect(0, 0, qrCodeWidth, qrCodeHeight);
      context.stroke();
    }

    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: "dontInvert",
    });
    const timestamp = parseFloat(code.data);
    return timestamp;
  };

  const updateRemoteCanvas = () => {
    const context = canvasRemoteRef.current.getContext("2d");
    const track = connection.remoteStream.getVideoTracks()[0];
    const processor = new window.MediaStreamTrackProcessor(track);
    const reader = processor.readable.getReader();

    const readRemoteFrame = async () => {
      const { done, value } = await reader.read();
      if (!value) {
        return;
      }
      // Resize canvas if necessary
      if (canvasRemoteRef.current.height !== value.displayHeight) {
        canvasRemoteRef.current.height = value.displayHeight;
      }
      if (canvasRemoteRef.current.width !== value.displayWidth) {
        canvasRemoteRef.current.width = value.displayWidth;
      }

      // context.clearRect(0, 0, canvasRemoteRef.current.width, canvasRemoteRef.current.height);
      context.drawImage(value, 0, 0);
      value.close();

      // Calculate latency for current frame
      await makeLogEntry();

      if (!done && !stopped.current) {
        readRemoteFrame();
      }
    };
    readRemoteFrame();
  };

  /** Get a video only local stream according to config */
  const getLocalStream = async () => {
    const constraints = {
      video: {
        width: { exact: config.width },
        height: { exact: config.height },
        frameRate: { exact: config.fps },
      },
      audio: false,
    };
    try {
      return await navigator.mediaDevices.getUserMedia(constraints);
    } catch (error) {
      console.error("Failed to open video camera. The constraints set in the config may be not possible.", error);
    }
  };

  const updateLocalCanvas = async () => {
    const context = canvasLocalRef.current.getContext("2d");
    const localBackgroundStream = await getLocalStream();
    if (!localBackgroundStream) throw new Error("Failed to get local stream");
    const track = localBackgroundStream.getVideoTracks()[0];
    const processor = new window.MediaStreamTrackProcessor(track);
    const reader = processor.readable.getReader();

    const readLocalFrame = async () => {
      const { done, value } = await reader.read();

      // Resize canvas if necessary
      if (canvasLocalRef.current.height !== value.displayHeight) {
        canvasLocalRef.current.height = value.displayHeight;
      }
      if (canvasLocalRef.current.width !== value.displayWidth) {
        canvasLocalRef.current.width = value.displayWidth;
      }

      // Put current VideoFrame on canvas
      // context.clearRect(0, 0, canvasLocalRef.current.width, canvasLocalRef.current.height);
      if (config.background) {
        context.drawImage(value, 0, 0);
      }

      // Put QRcode on canvas
      const timestamp = window.performance.now();
      QRCode.toCanvas(canvasQRRef.current, `${timestamp}`, { width: config.qrCodeSize });
      context.drawImage(canvasQRRef.current, 0, 0);

      // Save time it toked to generate the code (latency error)
      const qrCodeGenerationTime = window.performance.now() - timestamp;
      localStreamData.push({
        timestamp,
        qrCodeGenerationTime
      });

      // Print time on white background
      if (config.printTime) {
        const text = timestamp.toFixed(10);
        const textWidth = context.measureText(text).width;
        context.fillStyle = "white";
        context.fillRect(config.qrCodeSize, 0, textWidth + 20, 30);
        context.font = "16px Arial";
        context.fillStyle = "black";
        context.fillText(text, 10 + config.qrCodeSize, 20);
      }

      value.close();
      if (!done && !stopped.current) {
        readLocalFrame();
      } else {
        localBackgroundStream.getTracks().forEach(track => track.stop());
      }
    };
    readLocalFrame();
  };

  if (!window.MediaStreamTrackProcessor) {
    return "This Page requires the MediaStreamTrackProcessor. See: https://developer.mozilla.org/en-US/docs/Web/API/MediaStreamTrackProcessor#browser_compatibility";
  }

  /** Download `data` as json file. */
  const downloadData = () => {
    // TODO include other datasets
    const dataString = JSON.stringify(mergedData);
    const aElem = document.createElement("a");
    const file = new Blob([dataString], { type: "text/json" });
    aElem.href = URL.createObjectURL(file);
    aElem.download = `latency-test-${new Date().toLocaleDateString()}.json`;
    aElem.click();
  };

  // Get the main action button. Start, Stop or Reload button.
  let mainActionBtn = <></>;
  switch (connectionState) {
    case ConnectionState.NEW:
      mainActionBtn = <button onClick={start}>Start Experiment</button>;
      break;
    case ConnectionState.CONNECTING:
    case ConnectionState.CONNECTED:
      mainActionBtn = <button onClick={stop} disabled={connection.state !== ConnectionState.CONNECTED}>Stop Experiment</button>;
      break;
    default:
      mainActionBtn = <button onClick={() => window.location.reload()}>Reload Page</button>;;
      break;
  }

  return (
    <div className="ConnectionTestPageWrapper">
      <h1>Connection Latency Test</h1>
      <p>Connection State:
        <span className={`connectionState ${ConnectionState[connectionState]}`}>{ConnectionState[connectionState]}</span>
      </p>
      <TestConfig
        start={start}
        config={config}
        defaultConfig={defaultConfig}
        setConfig={setConfig}
        disabled={connectionState !== ConnectionState.NEW}
      />
      <div className="container controls">
        {mainActionBtn}
      </div>

      <button onClick={() => console.log(connection)}>Log Connection</button>

      <canvas ref={canvasQRRef} hidden />
      <div className="canvasWrapper">
        <div>
          <label>Local Stream</label>
          <canvas ref={canvasLocalRef} />
        </div>
        <div>
          <label>Remote Stream</label>
          <canvas ref={canvasRemoteRef} />
        </div>
      </div>

      <p>Latency: <span ref={latencyRef}>unknown</span> ms</p>

      {connectionState === ConnectionState.CLOSED ?
        mergedData ?
          <>
            <button onClick={downloadData}>Download Complete Dataset</button>
            <Evaluation mergedData={mergedData} />
          </>
          : "Waiting for Merged Data"
        : "Start and Stop Experiment to see results here."}
    </div >
  );
};


export default ConnectionLatencyTest;

type TestConfigObj = {
  participantId: string,
  sessionId: string,
  fps: number,
  background: boolean,
  width: number,
  height: number,
  qrCodeSize: number,
  printTime: boolean,
  outlineQrCode: boolean,
};

function TestConfig(props: {
  disabled?: boolean,
  config: TestConfigObj,
  defaultConfig: TestConfigObj,
  setConfig: (config: TestConfigObj) => void,
  start: () => void,
}) {
  const disabled = props.disabled ?? false;
  const config = props.config;

  const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    props.start();
  };

  const handleChange = (key: keyof TestConfigObj, value: string | number | boolean) => {
    const newConfig = { ...props.config };
    // @ts-ignore
    newConfig[key] = value;
    props.setConfig(newConfig);
    console.log("set", key, "to", value, newConfig);
  };

  // TODO hotkeys & reset btn

  return (
    <form onSubmit={handleSubmit} className="testConfig container">
      <Input disabled={disabled} label="Session ID" defaultValue={config.sessionId} setValue={(v) => handleChange("sessionId", v)} />
      <Input disabled={disabled} label="Participant ID" defaultValue={config.participantId} setValue={(v) => handleChange("participantId", v)} />
      <Input disabled={disabled} label="Frames per Second" type="number" defaultValue={config.fps} setValue={(v) => handleChange("fps", v)} />
      <Input disabled={disabled} label="Background Video" type="checkbox" defaultChecked={config.background} setValue={(v) => handleChange("background", v)} />
      <Input disabled={disabled} label="Video width (px)" type="number" defaultValue={config.width} setValue={(v) => handleChange("width", v)} />
      <Input disabled={disabled} label="Video height (px)" type="number" defaultValue={config.height} setValue={(v) => handleChange("height", v)} />
      <Input disabled={disabled} label="QR Code Size (px)" type="number" defaultValue={config.qrCodeSize} setValue={(v) => handleChange("qrCodeSize", v)} />
      <Input disabled={disabled} label="Print Time" type="checkbox" defaultChecked={config.printTime} setValue={(v) => handleChange("printTime", v)} />
      <Input disabled={disabled} label="Outline QR Code (Debug)" type="checkbox" defaultChecked={config.outlineQrCode} setValue={(v) => handleChange("outlineQrCode", v)} />
      <button type="submit" disabled={disabled} hidden />
    </form>
  );
}


function Evaluation(props: {
  mergedData: MergedData[];
}) {
  const [evaluation, setEvaluation] = useState<EvaluationResults | undefined>();
  const [from, setFrom] = useState(0);
  const [to, setTo] = useState(props.mergedData.length);
  const [primaryChart, setPrimaryChart] = useState<Chart | undefined>();
  const [fpsChart, setFpsChart] = useState<Chart | undefined>();
  const [dimensionsChart, setDimensionsChart] = useState<Chart | undefined>();
  const primaryChartCanvasRef = useRef<HTMLCanvasElement>();
  const fpsChartCanvasRef = useRef<HTMLCanvasElement>();
  const dimensionsChartCanvasRef = useRef<HTMLCanvasElement>();

  useEffect(() => {
    // From http://portal.mytum.de/corporatedesign/index_print/vorlagen/index_farben
    const colors = {
      TUMBlue: "#0065BD",
      TUMSecondaryBlue: "#005293",
      TUMSecondaryBlue2: "#003359",
      TUMBlack: "#000000",
      TUMWhite: "#FFFFFF",
      TUMDarkGray: "#333333",
      TUMGray: "#808080",
      TUMLightGray: "#CCCCC6",
      TUMAccentGray: "#DAD7CB",
      TUMAccentOrange: "#E37222",
      TUMAccentGreen: "#A2AD00",
      TUMAccentLightBlue: "#98C6EA",
      TUMAccentBlue: "#64A0C8",
    };

    /** Initialize Charts */
    const initCharts = () => {
      const { primaryData, primaryOptions, fpsData, fpsOptions, dimensionsData, dimensionsOptions } = getChartData();
      const newPrimaryChart = new Chart(
        primaryChartCanvasRef.current,
        {
          type: "line",
          data: primaryData,
          options: primaryOptions
        }
      );
      const newFpsChart = new Chart(
        fpsChartCanvasRef.current,
        {
          type: "line",
          data: fpsData,
          options: fpsOptions,
        }
      );
      const newDimensionsChart = new Chart(
        dimensionsChartCanvasRef.current,
        {
          type: "line",
          data: dimensionsData,
          options: dimensionsOptions
        }
      );
      setPrimaryChart(newPrimaryChart);
      setFpsChart(newFpsChart);
      setDimensionsChart(newDimensionsChart);
    };

    /** Update existing Charts */
    const updateCharts = () => {
      const { primaryData, fpsData, dimensionsData } = getChartData();

      primaryChart.data.labels = primaryData.labels;
      primaryChart.data.datasets = primaryData.datasets;
      primaryChart.update();

      fpsChart.data.labels = fpsData.labels;
      fpsChart.data.datasets = fpsData.datasets;
      fpsChart.update();

      dimensionsChart.data.labels = dimensionsData.labels;
      dimensionsChart.data.datasets = dimensionsData.datasets;
      dimensionsChart.update();
    };

    const getChartData = () => {
      const slicedData = props.mergedData.slice(from, to);
      const labels = slicedData.map(d => d.frame);
      const primaryData = {
        labels: labels,
        datasets: [
          // {
          //   label: "Latency-Error (WIP based on wrong data)",
          //   backgroundColor: colors.TUMAccentBlue,
          //   borderColor: colors.TUMAccentBlue,
          //   data: slicedData.map(d => d.latency - d.latencyMethodRuntime),
          //   fill: false,
          // }, 
          {
            label: "Latency",
            backgroundColor: colors.TUMBlue,
            borderColor: colors.TUMBlue,
            data: slicedData.map(d => d.latency),
            // fill: 0,
          }, {
            label: "True Latency",
            backgroundColor: colors.TUMAccentLightBlue,
            borderColor: colors.TUMAccentLightBlue,
            data: slicedData.map(d => d.trueLatency),
            hidden: true,
          }, {
            label: "Latency Method Runtime",
            backgroundColor: colors.TUMDarkGray,
            borderColor: colors.TUMDarkGray,
            data: slicedData.map(d => d.latencyMethodRuntime),
            hidden: true,
          }, {
            label: "QR Code Generation Runtime",
            backgroundColor: colors.TUMAccentOrange,
            borderColor: colors.TUMAccentOrange,
            data: slicedData.map(d => d.qrCodeGenerationTime),
            hidden: true,
          }
        ],
      };
      const primaryOptions = {
        animation: {
          duration: 0
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: "Frame Number"
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: "Milliseconds (ms)"
            },
            beginAtZero: true
          }
        }
      };

      const fpsData = {
        labels: labels,
        datasets: [{
          label: "Frames Per Second",
          backgroundColor: colors.TUMAccentGreen,
          borderColor: colors.TUMAccentGreen,
          data: slicedData.map(d => d.fps),
        }],
      };

      const fpsOptions = {
        maintainAspectRatio: false,
        animation: {
          duration: 0
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: "Frame Number"
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: "Current Frames Per Second"
            },
          }
        }
      };

      const dimensionsData = {
        labels: labels,
        datasets: [{
          label: "Width",
          backgroundColor: colors.TUMBlue,
          borderColor: colors.TUMBlue,
          data: slicedData.map(d => d.dimensions.width),
        }, {
          label: "Height",
          backgroundColor: colors.TUMAccentOrange,
          borderColor: colors.TUMAccentOrange,
          data: slicedData.map(d => d.dimensions.height),
        }],
      };

      const dimensionsOptions = {
        maintainAspectRatio: false,
        animation: {
          duration: 0
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: "Frame Number"
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: "Dimension in Pixel"
            },
          }
        }
      };

      return { primaryData, primaryOptions, fpsData, fpsOptions, dimensionsData, dimensionsOptions };
    };

    if (!primaryChartCanvasRef.current || !fpsChartCanvasRef.current) {
      return;
    }

    if (primaryChart) {
      updateCharts();
    } else {
      initCharts();
    }

  }, [from, to, props.mergedData, primaryChart, fpsChart, dimensionsChart]);

  useEffect(() => {
    if (from > to || from < 0 || to > props.mergedData.length) {
      console.warn(`Ignoring invalid data interval: ${from} - ${to}.`);
      return;
    }
    const slicedData = props.mergedData.slice(from, to);
    setEvaluation(calculateEvaluation(slicedData));
  }, [props.mergedData, from, to,]);


  /** Calculates EvaluationResults based on `data`. Slice `data` to set interval. */
  function calculateEvaluation(data: MergedData[]): EvaluationResults {
    // duration
    const durationTotalMs = (data[data.length - 1].timestamp - data[0].timestamp);
    const durationSec = Math.floor((durationTotalMs / 1000) % 60);
    const durationMin = Math.floor((durationTotalMs / 1000) / 60);
    const durationMs = durationTotalMs % 1000;

    // latency
    const invalidLatencyDataPoints = data.map(entry => entry.latency).filter(l => l === null).length;
    const invalidLatencyDataPointsPercent = Math.round((invalidLatencyDataPoints / data.length) * 100);
    const latencyArr = data.map(entry => entry.latency).filter(l => l !== null);
    const avgLatency = avg(latencyArr);
    const medianLatency = median(latencyArr);

    // True / corrected latency
    const trueLatencyArr = data.map(entry => entry.trueLatency).filter(l => l !== null);
    const avgTrueLatency = avg(trueLatencyArr);
    const medianTrueLatency = median(trueLatencyArr);

    // fps
    const fpsArr = data.map(entry => entry.fps);
    const avgFps = avg(fpsArr);
    const medianFps = median(fpsArr);

    // QR code generation
    const qrCodeGenTimeArr = data.map(d => d.qrCodeGenerationTime);
    const qrCodeGenTimeArrFiltered = qrCodeGenTimeArr.filter(t => t !== null);
    const missingQRCodeGenDataPoints = qrCodeGenTimeArr.length - qrCodeGenTimeArrFiltered.length;
    const missingQRCodeGenDataPointsPercent = Math.round((missingQRCodeGenDataPoints / data.length) * 100);
    const avgQrCodeGenTime = avg(qrCodeGenTimeArrFiltered);
    const medianQrCodeGenTime = median(qrCodeGenTimeArrFiltered);

    // Latency method / qr code parsing method
    const latencyMethodArr = data.map(entry => entry.latencyMethodRuntime);
    const avgLatencyMethod = avg(latencyMethodArr);
    const medianLatencyMethod = median(latencyMethodArr);

    console.group("Evaluation");
    console.log(`Data Points: ${data.length}`);
    console.log(`Duration: ${durationMin}m, ${durationSec}s, ${durationMs}ms`);
    console.log(`Invalid Latency Data Points: ${invalidLatencyDataPoints} (${invalidLatencyDataPointsPercent}%)`);
    console.log("Average Latency:", avgLatency, "ms");
    console.log("Median Latency:", medianLatency, "ms");
    console.log("Average FPS:", avgFps);
    console.log("Median FPS:", medianFps);

    console.group("QR Code Generation Time - Does affect latency");
    console.log(`Missing QR Code generation Data Points: ${missingQRCodeGenDataPoints} (${missingQRCodeGenDataPointsPercent}%)`);
    console.log("Average QR Code generation time:", avgQrCodeGenTime, "ms");
    console.log("Median QR Code generation time:", medianQrCodeGenTime, "ms");
    console.groupEnd();

    console.group("QR Code Parsing Time - Does not directly affect latency");
    console.log("Average Latency Method Runtime:", avgLatencyMethod, "ms");
    console.log("Median Latency Method Runtime:", medianLatencyMethod, "ms");
    console.groupEnd();

    console.groupEnd();

    return {
      dataPoints: data.length,
      durationTotalMs,
      durationSec,
      durationMin,
      durationMs,
      invalidLatencyDataPoints,
      invalidLatencyDataPointsPercent,
      avgLatency,
      medianLatency,
      avgTrueLatency,
      medianTrueLatency,
      missingQRCodeGenDataPoints,
      missingQRCodeGenDataPointsPercent,
      avgQrCodeGenTime,
      medianQrCodeGenTime,
      avgLatencyMethod,
      medianLatencyMethod,
      avgFps,
      medianFps
    };
  }

  return (
    <div>
      <h1>Evaluation</h1>
      <form className="evaluationInput">
        <span><b>Data Interval:</b>&nbsp;</span>
        <Input label="From" type="number" value={from} setValue={setFrom} min={0} max={to} />
        <Input label="To" type="number" value={to} setValue={setTo} min={from} max={props.mergedData.length} />
      </form>
      <h2>Overview</h2>
      {evaluation ?
        <>
          <div className="evaluationOverview">
            <label>Data Points: </label><span>{evaluation.dataPoints}</span>
            <label>Duration: </label><span>{evaluation.durationMin}m,&nbsp;{evaluation.durationSec}s,&nbsp;{evaluation.durationMs}ms</span>
            <label>Invalid Latency Data Points*: </label><span>{evaluation.invalidLatencyDataPoints} ({evaluation.invalidLatencyDataPointsPercent}%)</span>
            <label>Average Latency: </label><span>{evaluation.avgLatency}ms</span>
            <label>Median Latency: </label><span>{evaluation.medianLatency}ms</span>
            <label>Average True Latency: </label><span>{evaluation.avgTrueLatency}ms</span>
            <label>Median True Latency: </label><span>{evaluation.medianTrueLatency}ms</span>
            <label>Average FPS: </label><span>{evaluation.avgFps}fps</span>
            <label>Median FPS: </label><span>{evaluation.medianFps}fps</span>
            <label>Missing QR Code generation Data Points**: </label><span>{evaluation.missingQRCodeGenDataPoints} ({evaluation.missingQRCodeGenDataPointsPercent}%)</span>
            <label>Average QR Code generation Time**: </label><span>{evaluation.avgQrCodeGenTime}ms</span>
            <label>Median QR Code generation Time**: </label><span>{evaluation.medianQrCodeGenTime}ms</span>
            <label>Average Latency Calculation Runtime***: </label><span>{evaluation.avgQrCodeGenTime}ms</span>
            <label>Median Latency Calculation Runtime***: </label><span>{evaluation.medianQrCodeGenTime}ms</span>
          </div>
          <p className="note">*:&nbsp;Invalid latency measurements, likely caused by the QR-Code detection / parsing failing. The cause for a failing QR-Code detection could be its size, especially when WebRTC reduces the frame size.</p>
          <p className="note">**:&nbsp;Runtime of QR Code generation before a frame is sent. Affects latency.</p>
          <p className="note">***:&nbsp;Runtime of latency calculation function, includes QR-Code parsing. Does not directly impact the measured latency, but can be an important factor for CPU utilization, which does impact the measured latency.</p>
        </>
        : ""
      }

      <p>Click the labels above the graphs to enable or disable the corresponding line.</p>
      <h2>Latency</h2>
      <canvas ref={primaryChartCanvasRef}></canvas>
      <h2>Frames Per Second (FPS)</h2>
      <div style={{ height: "min(250px, 30vh)", position: "relative" }}>
        <canvas ref={fpsChartCanvasRef}></canvas>
      </div>
      <h2>Video Dimensions</h2>
      <div style={{ height: "min(250px, 30vh)", position: "relative" }}>
        <canvas ref={dimensionsChartCanvasRef}></canvas>
      </div>
    </div>
  );
}

function Input(props: {
  label: string,
  setValue: (value: any) => void;
  type?: string,
  disabled?: boolean,
  value?: string | number,
  defaultValue?: string | number,
  defaultChecked?: boolean,
  min?: number,
  max?: number,
}) {
  const handleChange = (e: any) => {
    let { value } = e.target;
    // Parse value to correct type
    if (props.type === "number") {
      value = parseInt(value) || 0;
    } else if (props.type === "checkbox") {
      value = e.target.checked;
    }
    props.setValue(value);
  };
  return (
    <>
      <label>{props.label}:</label>
      <input
        disabled={props.disabled}
        type={props.type ?? "text"}
        value={props.value}
        defaultValue={props.defaultValue}
        defaultChecked={props.defaultChecked}
        onChange={handleChange}
        min={props.min}
        max={props.max}
      />
    </>
  );
}
