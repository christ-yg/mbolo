import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function LoginScreen() {
  return <SafeAreaView style={styles.page}><View style={styles.card}>
    <Text style={styles.eyebrow}>CONNEXION MBOLO</Text>
    <Text style={styles.title}>Heureux de te revoir.</Text>
    <Text style={styles.copy}>Le formulaire sécurisé sera branché sur l'API Django au prochain lot.</Text>
    <Link href="/" style={styles.link}>← Retour à l'accueil</Link>
  </View></SafeAreaView>;
}
const styles = StyleSheet.create({
  page: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#21150f" },
  card: { padding: 28, borderRadius: 24, backgroundColor: "#fff8ef" },
  eyebrow: { color: "#e9543d", fontSize: 11, fontWeight: "900", letterSpacing: 1.5 },
  title: { marginTop: 12, color: "#21150f", fontSize: 34, fontWeight: "900" },
  copy: { marginTop: 14, color: "#7a675e", fontSize: 16, lineHeight: 24 },
  link: { marginTop: 28, color: "#e9543d", fontWeight: "800" },
});
