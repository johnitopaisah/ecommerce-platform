"use client";

import { useAuthStore } from "@/store/authStore";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/services";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const profileSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  about: z.string().max(500).optional(),
  phone_number: z.string().max(20).optional(),
  address_line_1: z.string().max(150).optional(),
  address_line_2: z.string().max(150).optional(),
  town_city: z.string().max(150).optional(),
  postcode: z.string().max(12).optional(),
  country: z.string().max(2).optional(),
});

const passwordSchema = z
  .object({
    old_password: z.string().min(1, "Current password is required"),
    new_password: z.string().min(8, "At least 8 characters"),
    new_password2: z.string().min(1, "Please confirm your password"),
  })
  .refine((d) => d.new_password === d.new_password2, {
    message: "Passwords do not match",
    path: ["new_password2"],
  });

type ProfileData = z.infer<typeof profileSchema>;
type PasswordData = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { user, fetchMe } = useAuthStore();
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const profileForm = useForm<ProfileData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      about: user?.about || "",
      phone_number: user?.phone_number || "",
      address_line_1: user?.address_line_1 || "",
      address_line_2: user?.address_line_2 || "",
      town_city: user?.town_city || "",
      postcode: user?.postcode || "",
      country: user?.country || "",
    },
  });

  // Re-populate form when user data arrives
  useEffect(() => {
    if (user) {
      profileForm.reset({
        first_name: user.first_name,
        last_name: user.last_name,
        about: user.about,
        phone_number: user.phone_number,
        address_line_1: user.address_line_1,
        address_line_2: user.address_line_2,
        town_city: user.town_city,
        postcode: user.postcode,
        country: user.country,
      });
    }
  }, [user]);

  const passwordForm = useForm<PasswordData>({
    resolver: zodResolver(passwordSchema),
  });

  const onProfileSubmit = async (data: ProfileData) => {
    try {
      await authApi.updateMe(data);
      await fetchMe();
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (err: any) {
      profileForm.setError("root", {
        message: err?.response?.data?.detail || "Update failed.",
      });
    }
  };

  const onPasswordSubmit = async (data: PasswordData) => {
    try {
      await authApi.changePassword(data);
      passwordForm.reset();
      setPasswordSuccess(true);
      setTimeout(() => setPasswordSuccess(false), 3000);
    } catch (err: any) {
      passwordForm.setError("root", {
        message: err?.response?.data?.detail || "Password change failed.",
      });
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Profile</h1>

      {/* Profile details */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="font-semibold text-gray-900 mb-5">Personal details</h2>
        <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              id="first_name"
              label="First name"
              {...profileForm.register("first_name")}
              error={profileForm.formState.errors.first_name?.message}
            />
            <Input
              id="last_name"
              label="Last name"
              {...profileForm.register("last_name")}
              error={profileForm.formState.errors.last_name?.message}
            />
          </div>

          {/* Read-only fields */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-500">Email</label>
              <p className="text-sm text-gray-400 bg-gray-50 rounded-lg px-3 py-2 border border-gray-200">
                {user?.email}
              </p>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-500">Username</label>
              <p className="text-sm text-gray-400 bg-gray-50 rounded-lg px-3 py-2 border border-gray-200">
                {user?.user_name}
              </p>
            </div>
          </div>

          <Input id="phone_number" label="Phone number" {...profileForm.register("phone_number")} />

          <h3 className="text-sm font-semibold text-gray-700 pt-2">Delivery address</h3>
          <Input id="address_line_1" label="Address line 1" {...profileForm.register("address_line_1")} />
          <Input id="address_line_2" label="Address line 2" {...profileForm.register("address_line_2")} />
          <div className="grid grid-cols-3 gap-4">
            <Input id="town_city" label="Town / City" {...profileForm.register("town_city")} />
            <Input id="postcode" label="Postcode" {...profileForm.register("postcode")} />
            <Input
              id="country"
              label="Country code"
              placeholder="e.g. GB"
              maxLength={2}
              {...profileForm.register("country")}
              error={profileForm.formState.errors.country?.message}
            />
          </div>

          {profileForm.formState.errors.root && (
            <p className="text-sm text-red-500">{profileForm.formState.errors.root.message}</p>
          )}
          {profileSuccess && (
            <p className="text-sm text-green-600">Profile updated successfully.</p>
          )}

          <Button
            type="submit"
            isLoading={profileForm.formState.isSubmitting}
          >
            Save changes
          </Button>
        </form>
      </div>

      {/* Change password */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="font-semibold text-gray-900 mb-5">Change password</h2>
        <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
          <Input
            id="old_password"
            label="Current password"
            type="password"
            {...passwordForm.register("old_password")}
            error={passwordForm.formState.errors.old_password?.message}
          />
          <Input
            id="new_password"
            label="New password"
            type="password"
            {...passwordForm.register("new_password")}
            error={passwordForm.formState.errors.new_password?.message}
          />
          <Input
            id="new_password2"
            label="Confirm new password"
            type="password"
            {...passwordForm.register("new_password2")}
            error={passwordForm.formState.errors.new_password2?.message}
          />

          {passwordForm.formState.errors.root && (
            <p className="text-sm text-red-500">{passwordForm.formState.errors.root.message}</p>
          )}
          {passwordSuccess && (
            <p className="text-sm text-green-600">Password changed successfully.</p>
          )}

          <Button type="submit" isLoading={passwordForm.formState.isSubmitting}>
            Change password
          </Button>
        </form>
      </div>
    </div>
  );
}
