// app/(main)/_layout.tsx
import { Stack } from 'expo-router';
import { CallProvider } from '../../contexts/CallContext'; // لاحظ تغيير المسار

export default function MainLayout() {
  return (
    // هنا نضع CallProvider ليغلف الشاشات الرئيسية فقط
    <CallProvider>
      <Stack>
        {/* هذه الشاشات الآن داخل نطاق CallProvider */}
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="call/[id]" options={{ headerShown: false }} />
      </Stack>
    </CallProvider>
  );
}
