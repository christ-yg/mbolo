import { Link } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

const promises = [
  ["Profils authentiques", "Une communauté construite autour de la confiance."],
  ["Rencontres proches", "Des connexions qui respectent les réalités africaines."],
  ["Sécurité d'abord", "Blocage, signalement et confidentialité dès le départ."],
] as const;

export default function WelcomeScreen() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.page} showsVerticalScrollIndicator={false}>
        <View style={styles.hero}>
          <View style={styles.brandRow}>
            <View style={styles.brandMark}><Text style={styles.brandMarkText}>M</Text></View>
            <Text style={styles.brand}>MBOLO</Text>
          </View>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>RENCONTRES AFRICAINES SÉRIEUSES</Text>
          </View>
          <Text style={styles.title}>
            La belle rencontre{"\n"}<Text style={styles.titleAccent}>commence ici.</Text>
          </Text>
          <Text style={styles.subtitle}>
            Découvre des personnes sincères, partage tes valeurs et construis
            une histoire qui te ressemble.
          </Text>
          <View style={styles.faces}>
            {["A", "N", "K", "S"].map((letter, index) => (
              <View key={letter} style={[styles.face, { marginLeft: index === 0 ? 0 : -12 }]}>
                <Text style={styles.faceText}>{letter}</Text>
              </View>
            ))}
            <Text style={styles.community}>Une communauté qui grandit</Text>
          </View>
        </View>

        <View style={styles.panel}>
          {promises.map(([title, description], index) => (
            <View key={title} style={styles.promise}>
              <View style={styles.promiseNumber}>
                <Text style={styles.promiseNumberText}>0{index + 1}</Text>
              </View>
              <View style={styles.promiseCopy}>
                <Text style={styles.promiseTitle}>{title}</Text>
                <Text style={styles.promiseDescription}>{description}</Text>
              </View>
            </View>
          ))}
          <Link href="/join" asChild>
            <Pressable accessibilityRole="button" style={({ pressed }) => [
              styles.primaryButton, pressed && styles.buttonPressed,
            ]}>
              <Text style={styles.primaryButtonText}>Créer mon profil</Text>
              <Text style={styles.primaryButtonArrow}>→</Text>
            </Pressable>
          </Link>
          <Link href="/login" asChild>
            <Pressable accessibilityRole="button" style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonText}>J'ai déjà un compte</Text>
            </Pressable>
          </Link>
          <Text style={styles.legal}>En continuant, tu confirmes avoir au moins 18 ans.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const c = { ink: "#21150f", cream: "#fff8ef", coral: "#e9543d", gold: "#f2b447" };
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: c.ink },
  page: { flexGrow: 1, backgroundColor: c.cream },
  hero: { minHeight: 470, paddingHorizontal: 28, paddingTop: 28, paddingBottom: 42, backgroundColor: c.ink },
  brandRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  brandMark: { width: 38, height: 38, borderRadius: 19, alignItems: "center", justifyContent: "center", backgroundColor: c.coral },
  brandMarkText: { color: "#fff", fontWeight: "900", fontSize: 20 },
  brand: { color: "#fff", fontSize: 20, fontWeight: "900", letterSpacing: 4 },
  badge: { alignSelf: "flex-start", marginTop: 48, paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999, backgroundColor: "rgba(242,180,71,0.14)" },
  badgeText: { color: c.gold, fontSize: 10, fontWeight: "800", letterSpacing: 1.2 },
  title: { marginTop: 20, color: "#fff", fontSize: 46, lineHeight: 50, fontWeight: "900", letterSpacing: -1.8 },
  titleAccent: { color: c.coral },
  subtitle: { maxWidth: 520, marginTop: 20, color: "#d8c9c0", fontSize: 17, lineHeight: 27 },
  faces: { flexDirection: "row", alignItems: "center", marginTop: 30 },
  face: { width: 42, height: 42, borderRadius: 21, borderWidth: 3, borderColor: c.ink, alignItems: "center", justifyContent: "center", backgroundColor: c.gold },
  faceText: { color: c.ink, fontWeight: "900" },
  community: { marginLeft: 12, color: "#bbaaa1", fontSize: 12 },
  panel: { width: "100%", maxWidth: 640, alignSelf: "center", paddingHorizontal: 24, paddingTop: 34, paddingBottom: 40 },
  promise: { flexDirection: "row", marginBottom: 22 },
  promiseNumber: { width: 44, height: 44, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: "#ffe2d8" },
  promiseNumberText: { color: c.coral, fontWeight: "900" },
  promiseCopy: { flex: 1, marginLeft: 15 },
  promiseTitle: { color: c.ink, fontSize: 16, fontWeight: "800" },
  promiseDescription: { marginTop: 4, color: "#7a675e", fontSize: 13, lineHeight: 19 },
  primaryButton: { minHeight: 58, marginTop: 8, borderRadius: 18, paddingHorizontal: 22, flexDirection: "row", alignItems: "center", justifyContent: "space-between", backgroundColor: c.coral },
  primaryButtonText: { color: "#fff", fontSize: 17, fontWeight: "800" },
  primaryButtonArrow: { color: "#fff", fontSize: 26 },
  buttonPressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
  secondaryButton: { alignItems: "center", paddingVertical: 18 },
  secondaryButtonText: { color: c.ink, fontSize: 15, fontWeight: "700" },
  legal: { color: "#9b8980", textAlign: "center", fontSize: 11 },
});
