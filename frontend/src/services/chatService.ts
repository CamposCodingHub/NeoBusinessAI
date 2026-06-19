import { addDoc, collection, serverTimestamp } from "firebase/firestore";
import { db } from "../lib/firebase";

export async function saveMessage(
  uid: string,
  chatId: string,
  text: string,
  role: "user" | "ai"
) {
  await addDoc(
    collection(db, "users", uid, "chats", chatId, "messages"),
    {
      text,
      role,
      createdAt: serverTimestamp(),
    }
  );
}