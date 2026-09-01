import { useRef, useState } from "react";
import "./App.css";

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState("Ready to record");
  const [profile, setProfile] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);


  // ==========================================
  // START RECORDING
  // ==========================================

  const startRecording = async () => {
    try {
      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      audioChunksRef.current = [];

      const mediaRecorder =
        new MediaRecorder(stream);

      console.log(
        "🎤 Microphone connected"
      );

      console.log(
        "Audio tracks:",
        stream.getAudioTracks()
      );

      console.log(
        "Recorder MIME type:",
        mediaRecorder.mimeType
      );

      mediaRecorderRef.current =
        mediaRecorder;


      // ==========================================
      // AUDIO DATA
      // ==========================================

      mediaRecorder.ondataavailable = (
        event
      ) => {

        console.log(
          "🎤 Audio data received:",
          event.data.size
        );

        if (event.data.size > 0) {

          audioChunksRef.current.push(
            event.data
          );

        }
      };


      // ==========================================
      // STOP RECORDING
      // ==========================================

      mediaRecorder.onstop = async () => {

        setStatus(
          "Processing voice..."
        );

        const audioBlob =
          new Blob(
            audioChunksRef.current,
            {
              type: "audio/webm",
            }
          );


        console.log(
          "🎵 Audio blob size:",
          audioBlob.size
        );


        stream
          .getTracks()
          .forEach((track) =>
            track.stop()
          );


        await sendAudioToBackend(
          audioBlob
        );
      };


      // ==========================================
      // START
      // ==========================================

      mediaRecorder.start();

      console.log(
        "▶️ Recording started"
      );

      setIsRecording(true);

      setStatus(
        "🎤 Listening... Speak now"
      );

    } catch (error) {

      console.error(
        "❌ Microphone error:",
        error
      );

      setStatus(
        "❌ Microphone permission denied or unavailable"
      );
    }
  };


  // ==========================================
  // STOP RECORDING
  // ==========================================

  const stopRecording = () => {

    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !==
        "inactive"
    ) {

      console.log(
        "⏹ Stopping recording..."
      );

      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);
  };


  // ==========================================
  // SEND AUDIO TO BACKEND
  // ==========================================

  const sendAudioToBackend = async (
    audioBlob
  ) => {

    try {

      setActionLoading(true);

      setStatus(
        "⏳ Processing voice..."
      );


      console.log(
        "📤 Sending audio to backend..."
      );


      const formData =
        new FormData();


      formData.append(
        "audio",
        audioBlob,
        "voice.webm"
      );


      const response =
        await fetch(
              "https://voice-profile-assistant.onrender.com/transcribe",

          {
            method: "POST",
            body: formData,
          }
        );


      const data =
        await response.json();


      console.log(
        "📥 Backend response:",
        data
      );


      // ==========================================
      // ERROR RESPONSE
      // ==========================================

      if (!response.ok) {

        setTranscript(
          data.transcript || ""
        );

        setProfile(
          data.profile || null
        );

        throw new Error(
          data.error ||
          "Voice processing failed"
        );
      }


      // ==========================================
      // PROFILE
      // ==========================================

      setProfile(
        data.profile || null
      );


      // ==========================================
      // TRANSCRIPT
      // ==========================================

      let cleanedTranscript =
        data.transcript || "";


      // ==========================================
      // CLEAN EMAIL IN DISPLAY
      // ==========================================

      if (
        data.profile &&
        data.profile.email
      ) {

        const email =
          data.profile.email
            .toLowerCase()
            .replace(/\s+/g, "");


        cleanedTranscript =
          cleanedTranscript.replace(

            /(?:my\s+)?email(?:\s+id)?\s+is\s+.*?(?=\s+(?:my|and|i\s+live|i\s+am|my\s+occupation|my\s+phone)|$)/i,

            `My email id is ${email}`
          );
      }


      setTranscript(
        cleanedTranscript
      );


      // ==========================================
      // ACTION STATUS
      // ==========================================

      if (
        data.action === "update"
      ) {

        setStatus(
          "✅ User updated successfully"
        );

      } else if (
        data.action === "delete"
      ) {

        setProfile(null);

        setStatus(
          "✅ User deleted successfully"
        );

      } else {

        setStatus(
          "✅ Profile created successfully"
        );
      }


    } catch (error) {

      console.error(
        "❌ Transcription error:",
        error
      );


      setStatus(
        `❌ ${error.message}`
      );

    } finally {

      setActionLoading(false);

    }
  };


  // ==========================================
  // UI
  // ==========================================

  return (

    <div className="app">

      <div className="card">


        {/* ==================================
            TITLE
        ================================== */}

        <h1>
          Voice User Profile
        </h1>


        <p className="subtitle">
          Speak naturally and create, update or delete your profile
        </p>


        {/* ==================================
            RECORD BUTTON
        ================================== */}

        <button

          className={
            isRecording
              ? "record-btn recording"
              : "record-btn"
          }

          onClick={
            isRecording
              ? stopRecording
              : startRecording
          }

          disabled={
            actionLoading
          }

        >

          {isRecording
            ? "⏹ Stop Recording"
            : "🎤 Start Recording"}

        </button>


        {/* ==================================
            STATUS
        ================================== */}

        <p className="status">
          {status}
        </p>


        {/* ==================================
            TRANSCRIPT
        ================================== */}

        <div className="transcript-box">

          <h2>
            Transcript
          </h2>


          <p>

            {transcript ||
              "Your voice transcript will appear here..."}

          </p>

        </div>


        {/* ==================================
            CURRENT USER PROFILE
        ================================== */}

        {profile && (

          <div className="profile-box">

            <h2>
              👤 User Profile
            </h2>


            {profile.name && (

              <p>

                <strong>
                  Name:
                </strong>{" "}

                {profile.name}

              </p>

            )}


            {profile.email && (

              <p>

                <strong>
                  ✉️ Email:
                </strong>{" "}

                {profile.email
                  .toLowerCase()
                  .replace(/\s+/g, "")}

              </p>

            )}


            {profile.phone && (

              <p>

                <strong>
                  📱 Phone:
                </strong>{" "}

                {profile.phone}

              </p>

            )}


            {profile.city && (

              <p>

                <strong>
                  📍 City:
                </strong>{" "}

                {profile.city}

              </p>

            )}


            {profile.occupation && (

              <p>

                <strong>
                  💼 Occupation:
                </strong>{" "}

                {profile.occupation}

              </p>

            )}

          </div>

        )}


        {/* ==================================
            TRY SAYING
        ================================== */}

       <div className="try-saying-box">

  <h2>Try saying</h2>

  <div className="try-section">

    <h3>Create</h3>

    <p>
      "My name is Anjali Gupta and my email is anjali at gmail dot com."
    </p>

  </div>


  <div className="try-section">

    <h3>Update</h3>

    <p>
      "Update Anjali's city to Jaipur."
    </p>

    <p>
      "Change Anjali's phone to 7668938153."
    </p>

    <p>
      "Change Anjali's occupation to React Developer."
    </p>

    <p>
      "Change Anjali's email to anjali123 at gmail dot com."
    </p>

  </div>


  <div className="try-section">

    <h3>Delete</h3>

    <p>
      "Delete Anjali."
    </p>

  </div>


  <div className="try-section">

    <h3>Show</h3>

    <p>
      "Show Anjali."
    </p>

    <p>
      "Show Anjali's profile."
    </p>

  </div>

</div>


      </div>

    </div>
  );
}

export default App;